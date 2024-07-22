import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useTheme } from '../contexts/ThemeContext';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/solid';

function LMPDetails() {
  const { id } = useParams();
  const [lmp, setLmp] = useState(null);
  const [versionHistory, setVersionHistory] = useState([]);
  const [invocations, setInvocations] = useState([]);
  const [expandedVersion, setExpandedVersion] = useState(null);
  const { darkMode } = useTheme();

  useEffect(() => {
    const fetchLMPDetails = async () => {
      try {
        const lmpResponse = await axios.get(`http://127.0.0.1:5000/api/lmps/${id}`);
        setLmp(lmpResponse.data);

        const versionHistoryResponse = await axios.get(`http://127.0.0.1:5000/api/lmps/${id}/versions`);
        setVersionHistory(versionHistoryResponse.data);

        const invocationsResponse = await axios.get(`http://127.0.0.1:5000/api/invocations/${id}`);
        setInvocations(invocationsResponse.data);
      } catch (error) {
        console.error('Error fetching LMP details:', error);
      }
    };
    fetchLMPDetails();
  }, [id]);

  if (!lmp) return <div className={`flex items-center justify-center h-screen ${darkMode ? 'bg-gray-900 text-gray-100' : 'bg-gray-100 text-gray-800'}`}>Loading...</div>;

  const toggleVersionExpand = (index) => {
    setExpandedVersion(expandedVersion === index ? null : index);
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gray-900 text-gray-100' : 'bg-gray-100 text-gray-800'}`}>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">{lmp.name}</h1>
        <div className={`bg-${darkMode ? 'gray-800' : 'white'} rounded-lg shadow-md p-6 mb-8`}>
          <p className="text-sm mb-4">ID: {lmp.lmp_id}</p>
          <h2 className="text-2xl font-semibold mb-4">Source Code</h2>
          <pre className={`bg-${darkMode ? 'gray-700' : 'gray-100'} p-4 rounded-md overflow-x-auto`}>
            <code>{lmp.source}</code>
          </pre>
          <div className="mt-6 grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-xl font-semibold mb-2">Details</h3>
              <p><strong>Created at:</strong> {new Date(lmp.created_at * 1000).toLocaleString()}</p>
              <p><strong>Is LMP:</strong> {lmp.is_lmp ? 'Yes' : 'No'}</p>
            </div>
            {lmp.lm_kwargs && (
              <div>
                <h3 className="text-xl font-semibold mb-2">LM Keywords</h3>
                <pre className={`bg-${darkMode ? 'gray-700' : 'gray-100'} p-4 rounded-md overflow-x-auto`}>
                  <code>{JSON.stringify(JSON.parse(lmp.lm_kwargs), null, 2)}</code>
                </pre>
              </div>
            )}
          </div>
        </div>
        <h2 className="text-2xl font-semibold mb-4">Version History</h2>
        <div className="space-y-4">
          {versionHistory.map((version, index) => (
            <div key={index} className={`bg-${darkMode ? 'gray-800' : 'white'} rounded-lg shadow-md overflow-hidden`}>
              <div 
                className={`p-4 cursor-pointer flex justify-between items-center ${expandedVersion === index ? `bg-${darkMode ? 'gray-700' : 'gray-200'}` : ''}`}
                onClick={() => toggleVersionExpand(index)}
              >
                <h3 className="text-xl font-semibold">Version {versionHistory.length - index}</h3>
                {expandedVersion === index ? (
                  <ChevronUpIcon className="h-5 w-5" />
                ) : (
                  <ChevronDownIcon className="h-5 w-5" />
                )}
              </div>
              {expandedVersion === index && (
                <div className="p-4 border-t border-gray-600">
                  <p><strong>LMP ID:</strong> {version.lmp_id}</p>
                  <p><strong>Created at:</strong> {new Date(version.created_at * 1000).toLocaleString()}</p>
                  <h4 className="font-semibold mt-2 mb-2">Source Code</h4>
                  <pre className={`bg-${darkMode ? 'gray-700' : 'gray-100'} p-4 rounded-md overflow-x-auto`}>
                    <code>{version.source}</code>
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
        <h2 className="text-2xl font-semibold mt-8 mb-4">Invocations</h2>
        <div className="space-y-4">
          {invocations.map((invocation, index) => (
            <div key={index} className={`bg-${darkMode ? 'gray-800' : 'white'} rounded-lg shadow-md overflow-hidden`}>
              <div 
                className={`p-4 cursor-pointer flex justify-between items-center ${expandedVersion === index ? `bg-${darkMode ? 'gray-700' : 'gray-200'}` : ''}`}
                onClick={() => toggleVersionExpand(index)}
              >
                <h3 className="text-xl font-semibold">Version {invocations.length - index}</h3>
                {expandedVersion === index ? (
                  <ChevronUpIcon className="h-5 w-5" />
                ) : (
                  <ChevronDownIcon className="h-5 w-5" />
                )}
              </div>
              {expandedVersion === index && (
                <div className="p-4 border-t border-gray-600">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p><strong>Args:</strong> {invocation.args}</p>
                      <p><strong>Kwargs:</strong> {invocation.kwargs}</p>
                      <p><strong>Result:</strong> {invocation.result}</p>
                      <p><strong>Created at:</strong> {new Date(invocation.created_at * 1000).toLocaleString()}</p>
                    </div>
                    <div>
                      <h4 className="font-semibold mb-2">Invocation Kwargs</h4>
                      <pre className={`bg-${darkMode ? 'gray-700' : 'gray-100'} p-4 rounded-md overflow-x-auto`}>
                        <code>{JSON.stringify(invocation.invocation_kwargs, null, 2)}</code>
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default LMPDetails;