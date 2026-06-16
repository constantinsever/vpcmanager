const AWS_REGION = "eu-central-1";
const COGNITO_CLIENT_ID = "m7b6hkunbnsd0gt80h803n6am";

window.onload = function () {
  const token = localStorage.getItem("access_token");

  if (token && !isTokenExpired(token)) {
    window.location.href = "dashboard.html";
  } else {
    clearSession();
    showLogin();
  }
};

function isTokenExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    const now = Math.floor(Date.now() / 1000);
    return payload.exp <= now;
  } catch {
    return true;
  }
}

function clearSession() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("cognito_session");
  localStorage.removeItem("challenge_username");
  localStorage.removeItem("pending_reset_email");
}

function hideForms() {
  ["loginForm", "newPasswordForm", "recoverForm", "resetPasswordForm"].forEach(id => {
    document.getElementById(id).classList.add("hidden");
  });
}

function showLogin() {
  hideForms();
  document.getElementById("loginForm").classList.remove("hidden");
  setMessage("");
}

function showRecover() {
  hideForms();
  document.getElementById("recoverForm").classList.remove("hidden");
  setMessage("");
}

function showNewPasswordForm() {
  hideForms();
  document.getElementById("newPasswordForm").classList.remove("hidden");
}

function showResetPasswordForm() {
  hideForms();
  document.getElementById("resetPasswordForm").classList.remove("hidden");
}

function setMessage(message) {
  document.getElementById("authMessage").textContent = message;
}

async function cognitoRequest(action, body) {
  const response = await fetch(`https://cognito-idp.${AWS_REGION}.amazonaws.com/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-amz-json-1.1",
      "X-Amz-Target": `AWSCognitoIdentityProviderService.${action}`
    },
    body: JSON.stringify(body)
  });

  const data = await response.json();
  console.log("Cognito action:", action);
  console.log("Cognito response:", data);

  if (!response.ok) {
    throw new Error(data.message || data.__type || "Cognito request failed");
  }

  return data;
}

async function login() {
  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value;

  if (!username || !password) {
    setMessage("Please enter username and password.");
    return;
  }

  setMessage("Logging in...");

  try {
    const data = await cognitoRequest("InitiateAuth", {
      AuthFlow: "USER_PASSWORD_AUTH",
      ClientId: COGNITO_CLIENT_ID,
      AuthParameters: {
        USERNAME: username,
        PASSWORD: password
      }
    });

    if (data.ChallengeName === "NEW_PASSWORD_REQUIRED") {
      localStorage.setItem("cognito_session", data.Session);
      localStorage.setItem("challenge_username", username);
      showNewPasswordForm();
      setMessage("First login detected. Please set a permanent password.");
      return;
    }

    if (!data.AuthenticationResult) {
      setMessage("Login failed. No authentication result returned.");
      return;
    }

    localStorage.setItem("access_token", data.AuthenticationResult.AccessToken);
    localStorage.setItem("id_token", data.AuthenticationResult.IdToken);
    window.location.href = "dashboard.html";

  } catch (error) {
    setMessage("Login failed: " + error.message);
  }
}

async function completeNewPassword() {
  const newPassword = document.getElementById("newPassword").value;
  const confirmPassword = document.getElementById("confirmNewPassword").value;

  if (!newPassword || !confirmPassword) {
    setMessage("Please enter and confirm the new password.");
    return;
  }

  if (newPassword !== confirmPassword) {
    setMessage("Passwords do not match.");
    return;
  }

  setMessage("Setting new password...");

  try {
    const data = await cognitoRequest("RespondToAuthChallenge", {
      ClientId: COGNITO_CLIENT_ID,
      ChallengeName: "NEW_PASSWORD_REQUIRED",
      Session: localStorage.getItem("cognito_session"),
      ChallengeResponses: {
        USERNAME: localStorage.getItem("challenge_username"),
        NEW_PASSWORD: newPassword
      }
    });

    localStorage.setItem("access_token", data.AuthenticationResult.AccessToken);
    localStorage.removeItem("cognito_session");
    localStorage.removeItem("challenge_username");

    window.location.href = "dashboard.html";

  } catch (error) {
    setMessage("Password setup failed: " + error.message);
  }
}

async function recoverPassword() {
  const username = document.getElementById("recoverEmail").value.trim();

  if (!username) {
    setMessage("Please enter your username.");
    return;
  }

  setMessage("Sending recovery code...");

  try {
    await cognitoRequest("ForgotPassword", {
      ClientId: COGNITO_CLIENT_ID,
      Username: username
    });

    localStorage.setItem("pending_reset_email", username);
    document.getElementById("resetEmail").value = username;

    showResetPasswordForm();
    setMessage("Recovery code sent. Check your email.");

  } catch (error) {
    setMessage("Recovery failed: " + error.message);
  }
}

async function confirmPasswordReset() {
  const username = document.getElementById("resetEmail").value.trim();
  const code = document.getElementById("resetCode").value.trim();
  const newPassword = document.getElementById("resetNewPassword").value;

  if (!username || !code || !newPassword) {
    setMessage("Please enter username, recovery code, and new password.");
    return;
  }

  setMessage("Resetting password...");

  try {
    await cognitoRequest("ConfirmForgotPassword", {
      ClientId: COGNITO_CLIENT_ID,
      Username: username,
      ConfirmationCode: code,
      Password: newPassword
    });

    localStorage.removeItem("pending_reset_email");
    showLogin();
    setMessage("Password reset successful. You can now log in.");

  } catch (error) {
    setMessage("Password reset failed: " + error.message);
  }
}