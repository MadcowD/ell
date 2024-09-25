import { useQuery, useQueryClient, useQueries } from "@tanstack/react-query";
import axios from "axios";
import { useEffect, useState } from "react";


const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? "http://localhost:5555" 
  : window.location.origin;

// Function to get WebSocket URL
const getWebSocketURL = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = process.env.NODE_ENV === 'development' ? 'localhost:5555' : window.location.host;
  console.log(host)
  return `${protocol}//${host}/ws`;
  
};

const WS_URL = getWebSocketURL();


export const useWebSocketConnection = () => {
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState(false);
  useEffect(() => {
    const socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      console.log("WebSocket connected");
      setIsConnected(true);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.entity === "database_updated") {
        // Invalidate relevant queries
        queryClient.invalidateQueries({ queryKey: ["traces"] });
        queryClient.invalidateQueries({ queryKey: ["latestLMPs"] });
        queryClient.invalidateQueries({ queryKey: ["invocations"] });
        queryClient.invalidateQueries({ queryKey: ["lmpDetails"] });
        console.log("Database updated, invalidating queries");
      }
    };

    socket.onclose = () => {
      console.log("WebSocket disconnected");
      setIsConnected(false);
    };

    return () => {
      console.log("WebSocket connection closed");
      socket.close();
    };
  }, [queryClient]);
  return { isConnected };
};

export const useLMPs = (name, id) => {
  return useQuery({
    queryKey: ["lmpDetails", name, id],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (name) params.append("name", name);
      if (id) params.append("lmp_id", id);

      const lmpResponse = await axios.get(
        `${API_BASE_URL}/api/lmps?${params.toString()}`
      );
      const all_lmps_matching = lmpResponse.data;
      return all_lmps_matching
        .map((lmp) => ({ ...lmp, created_at: new Date(lmp.created_at) }))
        .sort((a, b) => b.created_at - a.created_at);
    },
  });
};

export const useInvocationsFromLMP = (
  name,
  id,
  page = 0,
  pageSize = 50,
  hierarchical = false,
  invocationId = null,
) => {
  const query = useQuery({
    queryKey: ["invocations", name, id, page, pageSize],
    queryFn: async () => {
      const skip = page * pageSize;
      const params = new URLSearchParams();
      if (name) params.append("lmp_name", name);
      if (id) params.append("lmp_id", id);
      if (invocationId) params.append("id", invocationId);
      params.append("skip", skip);
      params.append("hierarchical", hierarchical);
      params.append("limit", pageSize);
      const response = await axios.get(
        `${API_BASE_URL}/api/invocations?${params.toString()}`
      );

      return response.data.sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at)
      );
    },
  });

  // if there are ant external blobs fetch them
  const [dataState, setDataState] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (query.data) {
      setDataState(query.data);
      setIsLoading(false);

      const fetchBlobs = async () => {
        query.data
          .filter((item) => item.contents.is_external)
          .forEach((item) => {
            fetchBlob(item.id).then((blob) => {
              setDataState((prevState) => {
                const updatedItem = prevState.find((i) => i.id === item.id);
                if (updatedItem) {
                  updatedItem.contents = blob;
                  updatedItem.contents.is_external_loaded = true;
                }
                return [...prevState];
              });
            });
          });
        //
      };
      fetchBlobs();
    }
  }, [query.data]);

  return { ...query, data: dataState, isLoading };
};

export const useInvocation = (id) => {
  const query = useInvocationsFromLMP(null, null, 0, 1, false, id);
  if(!id) return {
    data: null,
    isLoading: false,
    isError: false,
    error: null,
  }
  
  return {...query, data: query.data?.[0], };
};

export const useLatestLMPs = (page = 0, pageSize = 100) => {
  return useQuery({
    queryKey: ["latestLMPs", page, pageSize],
    queryFn: async () => {
      const skip = page * pageSize;
      const response = await axios.get(
        `${API_BASE_URL}/api/latest/lmps?skip=${skip}&limit=${pageSize}`
      );
      return response.data;
    },
  });
};



export const useTraces = (lmps) => {
  return useQuery({
    queryKey: ["traces", lmps],
    queryFn: async () => {
      const baseUrl = API_BASE_URL;
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
      const lmpIds = new Set(lmps.map((lmp) => lmp.lmp_id));
      const filteredTraces = uniqueTracesArray.filter(
        (trace) => lmpIds.has(trace.consumed) && lmpIds.has(trace.consumer)
      );

      return filteredTraces;
    },
    enabled: !!lmps && lmps.length > 0,
  });
};

export const useLMPHistory = (days = 365) => {
  return useQuery({
    queryKey: ["lmpHistory", days],
    queryFn: async () => {
      const response = await axios.get(
        `${API_BASE_URL}/api/lmp-history?days=${days}`
      );
      return response.data;
    },
  });
};

export const useInvocationsAggregate = (lmpName, lmpId, days = 30) => {
  return useQuery({
    queryKey: ["invocationsAggregate", lmpName, lmpId, days],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (lmpName) params.append("lmp_name", lmpName);
      if (lmpId) params.append("lmp_id", lmpId);
      params.append("days", days);
      const response = await axios.get(
        `${API_BASE_URL}/api/invocations/aggregate?${params.toString()}`
      );
      return response.data;
    },
  });
};
const fetchBlob = async (id) => {
  const response = await axios.get(`${API_BASE_URL}/api/blob/${id}`);
  return response.data;
};

export const useBlob = (id) => {
  return useQuery({
    queryKey: ["blob", id],
    queryFn: () => fetchBlob(id),
    enabled: !!id,
  });
};
