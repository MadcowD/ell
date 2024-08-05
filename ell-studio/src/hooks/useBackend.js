import { useQuery } from '@tanstack/react-query';
import axios from 'axios';


const API_BASE_URL = "http://localhost:8080";

export const useLMPDetails = (name, id) => {
  return useQuery({
    queryKey: ['lmpDetails', name, id],
    queryFn: async () => {
      const lmpResponse = await axios.get(`${API_BASE_URL}/api/lmps/${name}${id ? `/${id}` : ""}`);
      const all_lmps_matching = lmpResponse.data;
      return all_lmps_matching
        .map((lmp) => ({ ...lmp, created_at: new Date(lmp.created_at) }))
        .sort((a, b) => b.created_at - a.created_at)[0];
    }
  });
};

export const useVersionHistory = (name, page = 0, pageSize = 100) => {
  return useQuery({
    queryKey: ['versionHistory', name, page, pageSize],
    queryFn: async () => {
      const skip = page * pageSize;
      const response = await axios.get(`${API_BASE_URL}/api/lmps/${name}?skip=${skip}&limit=${pageSize}`);
      return (response.data || []).sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }
  });
};

export const useInvocations = (name, id, page = 0, pageSize = 100) => {
  return useQuery({
    queryKey: ['invocations', name, id, page, pageSize],
    queryFn: async () => {
      const skip = page * pageSize;
      const response = await axios.get(`${API_BASE_URL}/api/invocations/${name ? name : ""}${name && id ? `/${id}` : ""}?skip=${skip}&limit=${pageSize}`);
      return response.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }
  });
};

export const useUses = (usesIds) => {
  return useQuery({
    queryKey: ['uses', usesIds],
    queryFn: async () => {
      return Promise.all(
        usesIds.map(async (use) => {
          const useResponse = await axios.get(`${API_BASE_URL}/api/lmps/${use}`);
          return useResponse.data[0];
        })
      );
    },
    enabled: !!usesIds && usesIds.length > 0,
  });
};

export const useAllInvocations = (page = 0, pageSize = 100) => {
  return useQuery({
    queryKey: ['allInvocations', page, pageSize],
    queryFn: async () => {
      const skip = page * pageSize;
      const response = await axios.get(`${API_BASE_URL}/api/invocations?skip=${skip}&limit=${pageSize}`);
      return response.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }
  });
};


export const useAllLMPs = (page = 0, pageSize = 100) => {
  return useQuery({
    queryKey: ['allLMPs', page, pageSize],
    queryFn: async () => {
      const skip = page * pageSize;
      const response = await axios.get(`${API_BASE_URL}/api/lmps?skip=${skip}&limit=${pageSize}`);
      const lmps = response.data;

      // Group LMPs by name
      const lmpGroups = lmps.reduce((acc, lmp) => {
        if (!acc[lmp.name]) {
          acc[lmp.name] = [];
        }
        acc[lmp.name].push(lmp);
        return acc;
      }, {});

      // Process each group
      return Object.values(lmpGroups).map(group => {
        const sortedVersions = group.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        const latestVersion = sortedVersions[0];

        return {
          ...latestVersion,
          versions: sortedVersions.map(version => ({
            ...version,
            created_at: new Date(version.created_at),
          })),
        };
      });
    }
  });
};


 const fetchTraces = async (lmps) => {
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



export const useTraces = (lmps) => {
    return useQuery({
      queryKey: ['traces', lmps],
      queryFn: () => fetchTraces(lmps),
      enabled: !!lmps && lmps.length > 0,
    });
  };

// New function for searching invocations
export const useSearchInvocations = (query, page = 0, pageSize = 100) => {
  return useQuery({
    queryKey: ['searchInvocations', query, page, pageSize],
    queryFn: async () => {
      const skip = page * pageSize;
      const response = await axios.post(`${API_BASE_URL}/api/invocations/search?q=${encodeURIComponent(query)}&skip=${skip}&limit=${pageSize}`);
      return response.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    },
    enabled: !!query,
  });
};