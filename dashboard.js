const API_BASE_URL = "https://73pjc5yqn1.execute-api.eu-central-1.amazonaws.com"


window.onload = async function () {
  const token = getAuthToken();

  if (!token || isTokenExpired(token)) {
    logout();
    return;
  }

  await loadVpcs();
};

function getAuthToken() {
  return localStorage.getItem("id_token");
}



function isTokenExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    const now = Math.floor(Date.now() / 1000);
    return payload.exp <= now;
  } catch {
    return true;
  }
}

function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("id_token");
  window.location.href = "index.html";
}

function goDashboard() {
  window.location.href = "dashboard.html";
}

function goAudit() {
  window.location.href = "audit.html";
}



function setMessage(message) {
  document.getElementById("dashboardMessage").textContent = message;
}

function getSelectedRegion() {
  return document.getElementById("regionSelect").value;
}

function clearSubnets() {
  document.getElementById("subnetList").innerHTML = "";
}

async function authenticatedFetch(url, method = "GET", body = null) {
  const token = getAuthToken();

  if (!token || isTokenExpired(token)) {
    logout();
    throw new Error("Session expired");
  }

  const request = {
    method: method,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    }
  };

  if (body !== null) {
    request.body = body;
  }

  const response = await fetch(url, request);

  if (response.status === 401 || response.status === 403) {
    logout();
    throw new Error("Unauthorized");
  }

  return response;
}

async function onRegionChange() {
  clearSubnets();
  await loadVpcs();
}

async function loadVpcs() {
  const region = getSelectedRegion();
  const vpcList = document.getElementById("vpcList");

  vpcList.innerHTML = "";
  setMessage("Loading VPCs...");

  try {
    const response = await authenticatedFetch(
      `${API_BASE_URL}/vpcs?region=${region}`
    );

    const vpcs = await response.json();

    if (!response.ok) {
      throw new Error(vpcs.message || vpcs.error || "Failed to load VPCs");
    }

    vpcs.forEach(function (vpc) {
      const option = document.createElement("option");
      option.value = vpc.vpc_id;
      option.textContent =
        `${vpc.name || "Unnamed VPC"} | ${vpc.vpc_id} | ${vpc.cidr}`;
      vpcList.appendChild(option);
    });

    setMessage(`Loaded ${vpcs.length} VPC(s).`);

  } catch (error) {
    setMessage("Failed to load VPCs: " + error.message);
  }
}

async function onVpcSelected() {
  await loadSubnets();
}

async function loadSubnets() {
  const region = getSelectedRegion();
  const vpcId = document.getElementById("vpcList").value;
  const subnetList = document.getElementById("subnetList");

  subnetList.innerHTML = "";

  if (!vpcId) {
    setMessage("Select a VPC first.");
    return;
  }

  setMessage("Loading subnets...");

  try {
    const response = await authenticatedFetch(
      `${API_BASE_URL}/vpcs/${vpcId}/subnets?region=${region}`
    );

    const subnets = await response.json();

    if (!response.ok) {
      throw new Error(subnets.message || subnets.error || "Failed to load subnets");
    }

    subnets.forEach(function (subnet) {
      const option = document.createElement("option");
      option.value = subnet.subnet_id;
      option.textContent =
        `${subnet.name || "Unnamed Subnet"} | ${subnet.subnet_id} | ${subnet.cidr} | ${subnet.availability_zone}`;
      subnetList.appendChild(option);
    });

    setMessage(`Loaded ${subnets.length} subnet(s).`);

  } catch (error) {
    setMessage("Failed to load subnets: " + error.message);
  }
}



function createVpc() {
  document.getElementById("vpcNameInput").value = "";
  document.getElementById("vpcCidrInput").value = "10.0.0.0/16";
  document.getElementById("vpcDialog").classList.remove("hidden");
}


function closeVpcDialog() {
  document.getElementById("vpcDialog").classList.add("hidden");
}

async function submitVpcDialog() {
  const region = getSelectedRegion();
  const name = document.getElementById("vpcNameInput").value.trim();
  const cidr = document.getElementById("vpcCidrInput").value.trim();

  if (!name || !cidr) {
    setMessage("Please enter VPC name and CIDR.");
    return;
  }

  try {
    setMessage("Creating VPC...");

    const response = await authenticatedFetch(
      `${API_BASE_URL}/vpcs`,
      "POST",
      JSON.stringify({ region, name, cidr })
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.message || result.error || "Failed to create VPC");
    }

    closeVpcDialog();
    await loadVpcs();

    setMessage(`VPC created: ${result.resource_id}`);

  } catch (error) {
    setMessage("Failed to create VPC: " + error.message);
  }
}

async function deleteVpc() {
  const region = getSelectedRegion();
  const vpcId = document.getElementById("vpcList").value;

  if (!vpcId) {
    setMessage("Select a VPC first.");
    return;
  }

  if (!confirm(`Delete VPC ${vpcId}?`)) {
    return;
  }

  try {
    setMessage("Deleting VPC...");

    const response = await authenticatedFetch(
      `${API_BASE_URL}/vpcs/${vpcId}?region=${region}`,
      "DELETE"
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.message || result.error || "Failed to delete VPC");
    }

    clearSubnets();
    await loadVpcs();
    setMessage(`VPC deleted: ${vpcId}`);

  } catch (error) {
    setMessage("Failed to delete VPC: " + error.message);
  }
}

function createSubnet() {
  const vpcId = document.getElementById("vpcList").value;
  
  if (!vpcId) {
    setMessage("Select a VPC first.");
    return;
  }

  const region = getSelectedRegion();

  document.getElementById("subnetNameInput").value = "";
  document.getElementById("subnetCidrInput").value = "10.0.1.0/24";
  document.getElementById("subnetAzInput").value = `${region}a`;

  document
    .getElementById("subnetDialog")
    .classList
    .remove("hidden");
}


function closeSubnetDialog() {

  document
    .getElementById("subnetDialog")
    .classList
    .add("hidden");
}


async function submitSubnetDialog() {

  const region = getSelectedRegion();

  const vpcId = document.getElementById("vpcList").value;

  const name =
    document
      .getElementById("subnetNameInput")
      .value
      .trim();

  const cidr =
    document
      .getElementById("subnetCidrInput")
      .value
      .trim();

  const az =
    document
      .getElementById("subnetAzInput")
      .value
      .trim();

  if (!name || !cidr || !az) {
    setMessage(
      "Please complete all subnet fields."
    );
    return;
  }

  try {

    setMessage("Creating subnet...");

    const response =
      await authenticatedFetch(
        `${API_BASE_URL}/vpcs/${vpcId}/subnets`,
        "POST",
        JSON.stringify({
          region: region,
          name: name,
          cidr: cidr,
          availability_zone: az
        })
      );

    const result =
      await response.json();

    if (!response.ok) {
      throw new Error(
        result.message ||
        result.error ||
        "Failed to create subnet"
      );
    }

    closeSubnetDialog();

    await loadSubnets();

    setMessage(
      `Subnet created: ${result.resource_id}`
    );

  } catch (error) {

    setMessage(
      "Failed to create subnet: " +
      error.message
    );
  }
}



async function deleteSubnet() {
  const region = getSelectedRegion();
  const subnetId = document.getElementById("subnetList").value;

  if (!subnetId) {
    setMessage("Select a subnet first.");
    return;
  }

  if (!confirm(`Delete subnet ${subnetId}?`)) {
    return;
  }

  try {
    setMessage("Deleting subnet...");

    const response = await authenticatedFetch(
      `${API_BASE_URL}/subnets/${subnetId}?region=${region}`,
      "DELETE"
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.message || result.error || "Failed to delete subnet");
    }

    await loadSubnets();
    setMessage(`Subnet deleted: ${subnetId}`);

  } catch (error) {
    setMessage("Failed to delete subnet: " + error.message);
  }
}

function goToAudit() {
  window.location.href = "audit.html";
}