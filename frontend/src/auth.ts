import type { CognitoUserPool, CognitoUserSession } from 'amazon-cognito-identity-js';

const poolId = import.meta.env.VITE_COGNITO_USER_POOL_ID as string | undefined;
const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID as string | undefined;
export const cloudAuthEnabled = Boolean(poolId && clientId);

// Keep Cognito out of the initial app bundle at runtime. Local development access should
// render without loading its browser SDK or requiring a Cognito configuration.
let poolPromise: Promise<CognitoUserPool> | null = null;
async function getPool(): Promise<CognitoUserPool> {
  if (!poolId || !clientId) {
    throw new Error('Cloud sign-in is not configured. Configure Cognito for real account access.');
  }
  if (!poolPromise) {
    poolPromise = import('amazon-cognito-identity-js').then(({ CognitoUserPool }) =>
      new CognitoUserPool({ UserPoolId: poolId, ClientId: clientId }),
    );
  }
  return poolPromise;
}

export type SessionUser = { username: string; localMode: boolean };

export async function signIn(username: string, password: string): Promise<SessionUser> {
  if (!cloudAuthEnabled) {
    throw new Error('Cloud sign-in is not configured. Configure Cognito for real account access.');
  }
  const [{ AuthenticationDetails, CognitoUser }, pool] = await Promise.all([
    import('amazon-cognito-identity-js'),
    getPool(),
  ]);
  return new Promise((resolve, reject) => {
    const user = new CognitoUser({ Username: username, Pool: pool });
    user.authenticateUser(new AuthenticationDetails({ Username: username, Password: password }), {
      onSuccess: () => resolve({ username, localMode: false }),
      onFailure: (error: Error) => reject(error),
      newPasswordRequired: () => reject(new Error('This account requires a new password. Complete password reset in Cognito and sign in again.')),
    });
  });
}

export async function signUp(username: string, password: string): Promise<void> {
  if (!cloudAuthEnabled) throw new Error('Configure a Cognito user pool for cloud sign-up.');
  const [{ CognitoUserAttribute }, pool] = await Promise.all([
    import('amazon-cognito-identity-js'),
    getPool(),
  ]);
  await new Promise<void>((resolve, reject) => {
    const attributes = [new CognitoUserAttribute({ Name: 'email', Value: username })];
    pool.signUp(username, password, attributes, [], (error) => error ? reject(error) : resolve());
  });
}

export async function confirmSignUp(username: string, code: string): Promise<void> {
  if (!cloudAuthEnabled) throw new Error('Configure a Cognito user pool first.');
  const [{ CognitoUser }, pool] = await Promise.all([
    import('amazon-cognito-identity-js'),
    getPool(),
  ]);
  await new Promise<void>((resolve, reject) => {
    const user = new CognitoUser({ Username: username, Pool: pool });
    user.confirmRegistration(code, true, (error) => error ? reject(error) : resolve());
  });
}

export function signOut(): void {
  if (!poolPromise) return;
  void poolPromise.then((pool) => pool.getCurrentUser()?.signOut()).catch(() => undefined);
}


export async function requestPasswordReset(username: string): Promise<void> {
  if (!cloudAuthEnabled) throw new Error('Configure a Cognito user pool before using password reset.');
  const [{ CognitoUser }, pool] = await Promise.all([
    import('amazon-cognito-identity-js'),
    getPool(),
  ]);
  await new Promise<void>((resolve, reject) => {
    const user = new CognitoUser({ Username: username, Pool: pool });
    user.forgotPassword({
      onSuccess: () => resolve(),
      onFailure: (error: Error) => reject(error),
      inputVerificationCode: () => resolve(),
    });
  });
}

export async function confirmPasswordReset(username: string, code: string, newPassword: string): Promise<void> {
  if (!cloudAuthEnabled) throw new Error('Configure a Cognito user pool before using password reset.');
  const [{ CognitoUser }, pool] = await Promise.all([
    import('amazon-cognito-identity-js'),
    getPool(),
  ]);
  await new Promise<void>((resolve, reject) => {
    const user = new CognitoUser({ Username: username, Pool: pool });
    user.confirmPassword(code, newPassword, {
      onSuccess: () => resolve(),
      onFailure: (error: Error) => reject(error),
    });
  });
}


export async function restoreSession(): Promise<SessionUser | null> {
  if (!cloudAuthEnabled) return null;
  try {
    const pool = await getPool();
    const user = pool.getCurrentUser();
    if (!user) return null;
    return await new Promise<SessionUser | null>((resolve) => {
      user.getSession((error: Error | null, session: CognitoUserSession | null) => {
        resolve(!error && session?.isValid() ? { username: user.getUsername(), localMode: false } : null);
      });
    });
  } catch {
    return null;
  }
}

export async function sessionToken(): Promise<string | null> {
  if (!cloudAuthEnabled) return null;
  try {
    const pool = await getPool();
    const user = pool.getCurrentUser();
    if (!user) return null;
    return await new Promise<string | null>((resolve) => {
      user.getSession((error: Error | null, session: CognitoUserSession | null) => {
        resolve(!error && session?.isValid() ? session.getIdToken().getJwtToken() : null);
      });
    });
  } catch {
    return null;
  }
}
