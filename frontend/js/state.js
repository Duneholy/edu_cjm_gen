export const state = {
  sessionId: null,
};

export function setSessionId(id) {
  state.sessionId = id;
}

export function getSessionId() {
  return state.sessionId;
}

export function resetSession() {
  state.sessionId = null;
}
