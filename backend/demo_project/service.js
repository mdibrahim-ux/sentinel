// Demonstration-only examples. This file intentionally contains unsafe patterns.
export function renderUserSnippet(target, snippet) {
  // Untrusted data is written to a raw HTML sink.
  target.innerHTML = snippet;
}

export function runExpression(input) {
  return eval(input);
}
