import axios from 'axios';

export const fetchLMPs = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/api/lmps');
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
    lmpMap.get(lmp.name).versions.push({
      lmp_id: lmp.lmp_id,
      created_at: lmp.created_at,
      invocations: lmp.invocations || 0
    });
  });
  return Array.from(lmpMap.values()).map(lmp => ({
    ...lmp,
    versions: lmp.versions.sort((a, b) => b.created_at - a.created_at)
  }));
};