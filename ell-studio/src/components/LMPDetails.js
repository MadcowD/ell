import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useTheme } from '../contexts/ThemeContext';
import { ChevronDownIcon, ChevronUpIcon, LinkIcon } from '@heroicons/react/24/solid';
import Prism from 'prismjs';
import 'prismjs/themes/prism-tomorrow.css'; // Dark theme
import 'prismjs/components/prism-jsx';

function LMPDetails() {
  const { id } = useParams();
  const [lmp, setLmp] = useState(null);
  const [versionHistory, setVersionHistory] = useState([]);
  const [invocations, setInvocations] = useState([]);
  const [uses, setUses] = useState([]);
  const [expandedSection, setExpandedSection] = useState(null);
  const { darkMode } = useTheme();
  console.log(uses)

  const API_BASE_URL = "http://localhost:8080"

  useEffect(() => {
    const fetchLMPDetails = async () => {
      try {
        const lmpResponse = await axios.get(`${API_BASE_URL}/api/lmps/${id}`);
        setLmp(lmpResponse.data);

        const versionHistoryResponse = await axios.get(`${API_BASE_URL}/api/lmps/${id}/versions`);
        setVersionHistory(versionHistoryResponse.data);

        const invocationsResponse = await axios.get(`${API_BASE_URL}/api/invocations/${id}`);
        
        const sortedInvocations = invocationsResponse.data.sort((a, b) => b.created_at - a.created_at);
        setInvocations(sortedInvocations);

        const usesIds = (lmpResponse.data.uses);
        const uses = usesIds.map(async (use) => {
          const useResponse = await axios.get(`${API_BASE_URL}/api/lmps/${use}`);
          return useResponse.data;
        });
        setUses(await Promise.all(uses));
      } catch (error) {
        console.error('Error fetching LMP details:', error);
      }
    };
    fetchLMPDetails();
  }, [id, API_BASE_URL]);

  useEffect(() => {
    // Highlight the code after the component mounts or updates
    Prism.highlightAll();
  }, [lmp]);

  if (!lmp) return <div className={`flex items-center justify-center h-screen ${darkMode ? 'bg-gray-900 text-gray-100' : 'bg-gray-100 text-gray-800'}`}>Loading...</div>;

  const toggleSectionExpand = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gray-900 text-gray-100' : 'bg-gray-100 text-gray-800'}`}>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">{lmp.name}</h1>
        <div className={`bg-${darkMode ? 'gray-800' : 'white'} rounded-lg shadow-md p-6 mb-8`}>
          <p className="text-sm mb-4">ID: {lmp.lmp_id}</p>
          <h2 className="text-2xl font-semibold mb-4">Source Code</h2>
          <pre className={`rounded-md overflow-x-auto ${darkMode ? 'bg-gray-800' : 'bg-gray-200'}`}>
            <code className="language-jsx">{(lmp.dependencies.trim() + '\n\n' + lmp.source).trim()}</code>
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
                  <code>{JSON.stringify((lmp.lm_kwargs), null, 2)}</code>
                </pre>
              </div>
            )}
          </div>
        </div>
        <h2 className="text-2xl font-semibold mt-8 mb-4">Version History</h2>
        <div className={`bg-${darkMode ? 'gray-800' : 'white'} rounded-lg shadow-md p-6 mb-8`}>
          <div 
            className="cursor-pointer flex justify-between items-center"
            onClick={() => toggleSectionExpand('versionHistory')}
          >
            <h3 className="text-xl font-semibold">Source Code Versions</h3>
            {expandedSection === 'versionHistory' ? (
              <ChevronUpIcon className="h-5 w-5" />
            ) : (
              <ChevronDownIcon className="h-5 w-5" />
            )}
          </div>
          {expandedSection === 'versionHistory' && (
            <div className="mt-4 space-y-4">
              {versionHistory.map((version, index) => (
                <div key={version.lmp_id} className="flex items-center">
                  <div className={`w-4 h-4 rounded-full ${darkMode ? 'bg-blue-500' : 'bg-blue-400'} mr-2`}></div>
                  <div>
                    <p className="text-sm font-semibold">Version {versionHistory.length - index}</p>
                    <p className="text-xs">{new Date(version.created_at * 1000).toLocaleString()}</p>
                    <p className="text-xs">Temporary commit message</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <h2 className="text-2xl font-semibold mt-8 mb-4">Uses (Dependencies)</h2>
        <div className={`bg-${darkMode ? 'gray-800' : 'white'} rounded-lg shadow-md p-6 mb-8`}>
          <h3 className="text-xl font-semibold mb-4">LMP Dependencies</h3>
          <div className="space-y-2">
            {uses.length > 0 ? (
              uses.map((use, index) => (
                <div key={use.lmp_id} className="flex items-center">
                  <LinkIcon className="h-5 w-5 mr-2" />
                  <Link to={`/lmp/${use.lmp_id}`} className="text-sm hover:underline">{use.name}()</Link>
                </div>
              ))
            ) : (
              <p>No dependencies on other LMPs.</p>
            )}
          </div>
        </div>
        <h2 className="text-2xl font-semibold mt-8 mb-4">Invocations</h2>
        <div className="space-y-4">
          {invocations.map((invocation, index) => (
            <div key={index} className={`bg-${darkMode ? 'gray-800' : 'white'} rounded-lg shadow-md overflow-hidden relative`}>
              <div 
                className={`p-4 cursor-pointer flex justify-between items-center`}
                onClick={() => toggleSectionExpand(`invocation-${index}`)}
              >
                <h3 className="text-xl font-semibold">Invocation {invocations.length - index}</h3>
                {expandedSection === `invocation-${index}` ? (
                  <ChevronUpIcon className="h-5 w-5" />
                ) : (
                  <ChevronDownIcon className="h-5 w-5" />
                )}
              </div>
              <span className={`absolute top-2 right-2 text-xs px-2 py-1 rounded-full ${darkMode ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-800'}`}>
                Version {versionHistory.findIndex(v => v.lmp_id === invocation.lmp_id) + 1}
              </span>
              {expandedSection === `invocation-${index}` && (
                <div className="p-4 border-t border-gray-600">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p><strong>Args:</strong> {JSON.stringify(invocation.args)}</p>
                      <p><strong>Kwargs:</strong> {JSON.stringify(invocation.kwargs)}</p>
                      <p><strong>Result:</strong> {JSON.stringify(invocation.result)}</p>
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