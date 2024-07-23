import axios from 'axios';

const API_BASE_URL = "http://localhost:8080"
export const fetchLMPs = async () => {
  try {
    const baseUrl = API_BASE_URL
    const response = await axios.get(`${baseUrl}/api/lmps`);
    return aggregateLMPsByName(response.data);
  } catch (error) {
    console.error('Error fetching LMPs:', error);
    throw error;
  }
};

export const aggregateLMPsByName = (lmpList) => {
  const lmpMap = new Map();
  lmpList.forEach(lmp => {
    if (!lmpMap.has(lmp.name)) {
      lmpMap.set(lmp.name, { ...lmp, versions: [] });
    }
    console.log(new Date(lmp.created_at))
    lmpMap.get(lmp.name).versions.push({
      lmp_id: lmp.lmp_id,
      created_at: new Date(lmp.created_at + 'Z'), // Parse the date string as UTC
      invocations: lmp.invocations || 0
    });
  });
  return Array.from(lmpMap.values()).map(lmp => ({
    ...lmp,
    versions: lmp.versions.sort((a, b) => b.created_at.getTime() - a.created_at.getTime())
  }));
};