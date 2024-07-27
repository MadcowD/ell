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
  const lmpsByName = new Map()
  const lmpNameById = new Map()
  lmpList.forEach(lmp => {
    const cleanedLmp = {
      ...lmp,
      created_at: new Date(lmp.created_at + 'Z'),
    }
    if (!lmpsByName.has(lmp.name)) {
      lmpsByName.set(lmp.name, [cleanedLmp]);
    } else {
      lmpsByName.get(lmp.name).push(cleanedLmp);
    }
    lmpNameById.set(lmp.lmp_id, lmp.name)
  });

  const latestLMPByName = new Map()
  lmpsByName.forEach((lmpVersions, lmpName) => {
    const latestLMP = lmpVersions.sort((a, b) => b.created_at - a.created_at)[0]
    latestLMPByName.set(lmpName, latestLMP)
  })

  // Now make a latest LMP by nam but add all the versions as a property on that lmp
  const latestLMPs = Array.from(latestLMPByName.values())
  latestLMPs.forEach(lmp => {
    lmp.versions = lmpsByName.get(lmp.name).sort((a, b) => b.created_at - a.created_at)
    // sanetize the uses of the lmp to only have the latest version of the lmp whose id has that name
    lmp.uses = lmp.uses.map(useId => {
      const useLmpName = lmpNameById.get(useId)
      return latestLMPByName.get(useLmpName).lmp_id
    })
  })
  
  return latestLMPs
};

export const fetchTraces = async (lmps) => {
  const baseUrl = API_BASE_URL
  const response = await axios.get(`${baseUrl}/api/traces`);
  // Filter out duplicate traces based on consumed and consumer
  const uniqueTraces = response.data.reduce((acc, trace) => {
    const key = `${trace.consumed}-${trace.consumer}`;
    if (!acc[key]) {
      acc[key] = trace;
    }
    return acc;
  }, {});

  // Convert the object of unique traces back to an array
  const uniqueTracesArray = Object.values(uniqueTraces);

  // Filter out traces between LMPs that are not on the graph
  const lmpIds = new Set(lmps.map(lmp => lmp.lmp_id));
  const filteredTraces = uniqueTracesArray.filter(trace => 
    lmpIds.has(trace.consumed) && lmpIds.has(trace.consumer)
  );
  
  return filteredTraces;
}


export function getTimeAgo(date) {
  const now = new Date();
  const secondsPast = (now.getTime() - date.getTime()) / 1000;
  if (secondsPast < 60) {
    return `${Math.round(secondsPast)} seconds ago`;
  }
  if (secondsPast < 3600) {
    return `${Math.round(secondsPast / 60)} minutes ago`;
  }
  if (secondsPast <= 86400) {
    return `${Math.round(secondsPast / 3600)} hours ago`;
  }
  if (secondsPast <= 2592000) {
    return `${Math.round(secondsPast / 86400)} days ago`;
  }
  if (secondsPast <= 31536000) {
    return `${Math.round(secondsPast / 2592000)} months ago`;
  }
  return `${Math.round(secondsPast / 31536000)} years ago`;
}

