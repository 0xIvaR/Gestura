import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 5000
});

export async function startGestureControl() {
  const { data } = await api.post('/start-gesture-control');
  return data;
}

export async function stopGestureControl() {
  const { data } = await api.post('/stop-gesture-control');
  return data;
}

export async function getStatus() {
  const { data } = await api.get('/status');
  return data;
}

export async function updateSettings(payload: {
  mode: 'Study' | 'General';
  smoothness: number;
  sensitivity: number;
  liveCameraPreview: boolean;
}) {
  const { data } = await api.post('/update-settings', payload);
  return data;
}



