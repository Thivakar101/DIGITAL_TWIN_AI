import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.166.1/build/three.module.js';
import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.166.1/examples/jsm/loaders/GLTFLoader.js';

const statusMode = document.querySelector('#statusMode');
const statusModel = document.querySelector('#statusModel');
const statusSignal = document.querySelector('#statusSignal');
const statusError = document.querySelector('#statusError');
const userName = document.querySelector('#userName');
const modelName = document.querySelector('#modelName');
const baseUrl = document.querySelector('#baseUrl');
const memoryTable = document.querySelector('#memoryTable');
const chatLog = document.querySelector('#chatLog');
const simulateOutput = document.querySelector('#simulateOutput');
const toast = document.querySelector('#toast');

function showToast(message, isError = false) {
  toast.hidden = false;
  toast.textContent = message;
  toast.style.borderColor = isError ? 'rgba(255, 179, 179, 0.4)' : 'rgba(255, 255, 255, 0.16)';
  toast.style.color = isError ? '#ffdcdc' : '#f7f7f7';
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    toast.hidden = true;
  }, 3400);
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Request failed');
  }
  return data;
}

function appendChat(role, text) {
  const item = document.createElement('div');
  item.className = `log-entry ${role}`;
  const speaker = role === 'user' ? 'You' : 'Chloe';
  item.innerHTML = `<strong>${speaker}</strong><p>${text}</p>`;
  chatLog.appendChild(item);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function updateStatus(status) {
  const mode = String(status.mode || 'offline').toUpperCase();
  statusMode.textContent = mode;
  statusModel.textContent = status.model_name || 'Unknown';
  statusSignal.textContent = status.last_error ? 'Attention Needed' : 'Synchronized';
  statusError.textContent = status.last_error || '';
  userName.value = status.user_name || '';
  if (modelName) modelName.value = status.model_name || '';
  if (baseUrl) baseUrl.value = status.base_url || '';
}

async function loadStatus() {
  const data = await request('/api/status');
  updateStatus(data);
}

async function loadMemories() {
  const data = await request('/api/memories');
  memoryTable.innerHTML = '';
  for (const memory of data.memories) {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${memory.type}</td>
      <td>${memory.text}</td>
      <td>${memory.timestamp}</td>
      <td>${JSON.stringify(memory.meta || {})}</td>
    `;
    memoryTable.appendChild(row);
  }
}

async function initOrb() {
  const canvas = document.querySelector('#orbCanvas');
  if (!canvas) {
    return;
  }

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100);
  camera.position.set(0, 0.05, 2.75);

  const rig = new THREE.Group();
  scene.add(rig);

  const halo = new THREE.Mesh(
    new THREE.TorusGeometry(1.32, 0.012, 18, 180),
    new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.18 })
  );
  halo.rotation.x = Math.PI / 2.35;
  halo.position.y = 0.02;
  scene.add(halo);

  const silhouette = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.SphereGeometry(1.05, 16, 16)),
    new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.06 })
  );
  silhouette.scale.set(0.88, 1.18, 0.82);
  silhouette.position.y = 0.02;
  scene.add(silhouette);

  scene.add(new THREE.AmbientLight(0xffffff, 1.5));
  const keyLight = new THREE.PointLight(0xffffff, 16, 24);
  keyLight.position.set(2.4, 1.2, 4.4);
  scene.add(keyLight);
  const fillLight = new THREE.PointLight(0xffffff, 5, 24);
  fillLight.position.set(-2.3, 0.8, 3.2);
  scene.add(fillLight);
  const rimLight = new THREE.PointLight(0xffffff, 7, 24);
  rimLight.position.set(0, -1.3, 2.2);
  scene.add(rimLight);

  const loader = new GLTFLoader();
  const gltf = await loader.loadAsync('https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/gltf/LeePerrySmith/LeePerrySmith.glb');
  const faceAsset = gltf.scene;

  faceAsset.traverse((node) => {
    if (!node.isMesh) {
      return;
    }
    node.material = new THREE.MeshPhysicalMaterial({
      color: 0xf1f1f1,
      roughness: 0.28,
      metalness: 0.62,
      clearcoat: 1,
      clearcoatRoughness: 0.12,
      emissive: 0x040404,
    });
  });

  faceAsset.scale.set(0.015, 0.015, 0.015);
  faceAsset.position.set(0, -1.18, 0.08);
  faceAsset.rotation.y = Math.PI;
  rig.add(faceAsset);

  const visor = new THREE.Mesh(
    new THREE.SphereGeometry(0.78, 48, 48),
    new THREE.MeshStandardMaterial({
      color: 0x111111,
      roughness: 0.76,
      metalness: 0.12,
      transparent: true,
      opacity: 0.88,
    })
  );
  visor.scale.set(0.68, 0.94, 0.3);
  visor.position.set(0, 0.04, 0.68);
  rig.add(visor);

  const leftEye = new THREE.Mesh(
    new THREE.CircleGeometry(0.07, 48),
    new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.76 })
  );
  leftEye.position.set(-0.25, 0.12, 0.9);
  rig.add(leftEye);

  const rightEye = leftEye.clone();
  rightEye.position.x = 0.25;
  rig.add(rightEye);

  const mouthLine = new THREE.Mesh(
    new THREE.TorusGeometry(0.16, 0.008, 10, 48, Math.PI * 0.82),
    new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.28 })
  );
  mouthLine.rotation.z = Math.PI;
  mouthLine.position.set(0, -0.36, 0.9);
  mouthLine.scale.y = 0.48;
  rig.add(mouthLine);

  const foreheadArc = new THREE.Mesh(
    new THREE.TorusGeometry(0.48, 0.018, 14, 64, Math.PI),
    new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.42 })
  );
  foreheadArc.rotation.z = Math.PI;
  foreheadArc.position.set(0, 0.52, 0.83);
  rig.add(foreheadArc);

  function resize() {
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(1, Math.floor(rect.width * window.devicePixelRatio));
    const height = Math.max(1, Math.floor(rect.height * window.devicePixelRatio));
    if (canvas.width !== width || canvas.height !== height) {
      renderer.setSize(rect.width, rect.height, false);
      camera.aspect = rect.width / rect.height;
      camera.updateProjectionMatrix();
    }
  }

  function animate(time) {
    resize();
    const t = time * 0.001;
    rig.rotation.y = Math.sin(t * 0.32) * 0.12;
    rig.rotation.x = Math.sin(t * 0.22) * 0.025 - 0.01;
    rig.position.y = Math.sin(t * 0.6) * 0.02;
    halo.rotation.z = t * 0.08;
    silhouette.rotation.y = -t * 0.09;
    leftEye.material.opacity = 0.68 + (Math.sin(t * 2.0) + 1) * 0.06;
    rightEye.material.opacity = 0.68 + (Math.cos(t * 2.0) + 1) * 0.06;
    foreheadArc.material.opacity = 0.38 + (Math.sin(t * 1.35) + 1) * 0.06;
    mouthLine.material.opacity = 0.22 + (Math.sin(t * 1.0) + 1) * 0.04;
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
  }

  requestAnimationFrame(animate);
}

document.querySelector('#settingsForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    user_name: userName.value.trim(),
    model_name: modelName.value.trim(),
    base_url: baseUrl.value.trim(),
  };
  try {
    const data = await request('/api/settings', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    updateStatus(data.status);
    showToast(data.message || 'Settings saved.');
  } catch (error) {
    showToast(error.message, true);
  }
});

document.querySelector('#surveyForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());
  for (const [key, value] of Object.entries(payload)) {
    if (/^(tone_|msg_length|humor_frequency|val_|agreeableness|conscientiousness|openness|extraversion|decision_|risk_tolerance|speed_vs_thoroughness|mbti_)/.test(key)) {
      payload[key] = Number(value || 3);
    }
  }
  try {
    const data = await request('/api/survey', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    updateStatus(data.status);
    await loadMemories();
    showToast(data.message || 'Persona synchronized.');
  } catch (error) {
    showToast(error.message, true);
  }
});

document.querySelector('#chatForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const input = document.querySelector('#chatMessage');
  const message = input.value.trim();
  if (!message) {
    return;
  }
  appendChat('user', message);
  input.value = '';
  try {
    const data = await request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
    appendChat('chloe', data.reply);
    await loadMemories();
  } catch (error) {
    appendChat('chloe', error.message);
    showToast(error.message, true);
  }
});

document.querySelector('#simulateForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = document.querySelector('#situation').value.trim();
  if (!message) {
    return;
  }
  simulateOutput.textContent = 'Chloe is evaluating the scenario...';
  try {
    const data = await request('/api/simulate', {
      method: 'POST',
      body: JSON.stringify({ situation: message }),
    });
    simulateOutput.textContent = data.reply;
    await loadMemories();
  } catch (error) {
    simulateOutput.textContent = error.message;
    showToast(error.message, true);
  }
});

document.querySelector('#refreshMemories').addEventListener('click', loadMemories);

Promise.all([loadStatus(), loadMemories()])
  .then(initOrb)
  .catch((error) => {
    statusMode.textContent = 'OFFLINE';
    statusSignal.textContent = 'Link Failed';
    statusError.textContent = error.message;
    showToast(error.message, true);
    initOrb();
  });
