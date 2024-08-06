import React, { useState, useEffect, useMemo } from "react";
import {
  useParams,
  useSearchParams,
  useNavigate,
  Link,
} from "react-router-dom";
import {
  useLMPs,
  useInvocationsFromLMP,
  useMultipleLMPs,
  useInvocation,
} from "../hooks/useBackend";
import InvocationsTable from "../components/invocations/InvocationsTable";
import DependencyGraphPane from "../components/DependencyGraphPane";
import LMPSourceView from "../components/source/LMPSourceView";
import { FiCopy, FiFilter, FiColumns, FiGitCommit } from "react-icons/fi";
import VersionHistoryPane from "../components/VersionHistoryPane";
import toast from "react-hot-toast";
import VersionBadge from "../components/VersionBadge";
import { LMPCardTitle } from "../components/depgraph/LMPCardTitle";
import InvocationsLayout from "../components/invocations/InvocationsLayout";
import ToggleSwitch from "../components/common/ToggleSwitch";
import LMPDetailsSidePanel from "../components/LMPDetailsSidePanel";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "../components/common/Resizable";
import { ScrollArea } from "../components/common/ScrollArea";

function LMP() {
  const { name, id } = useParams();
  let [searchParams, setSearchParams] = useSearchParams();
  const requestedInvocationId = searchParams.get("i");

  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 50;

  // TODO: Could be expensive if you have a funct on of versions.
  const { data: versionHistory, isLoading: isLoadingLMP } = useLMPs(name);
  const lmp = useMemo(() => {
    if (!versionHistory) return null;
    if (id) {
      return versionHistory.find((v) => v.lmp_id === id);
    } else {
      return versionHistory[0];
    }
  }, [versionHistory, id]);

  const { data: invocations } = useInvocationsFromLMP(
    name,
    id,
    currentPage,
    pageSize
  );
  const { data: uses } = useMultipleLMPs(lmp?.uses);

  const [activeTab, setActiveTab] = useState("runs");
  const [selectedTrace, setSelectedTrace] = useState(null);
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState("Source");

  const previousVersion = useMemo(() => {
    if (!versionHistory) return null;
    const currentVersionIndex = versionHistory.findIndex(
      (v) => v.lmp_id === lmp?.lmp_id
    );
    return versionHistory.length > 1 &&
      currentVersionIndex < versionHistory.length - 1
      ? versionHistory[currentVersionIndex + 1]
      : null;
  }, [versionHistory, lmp]);

  const { data: requestedInvocationQueryData } = useInvocation(
    requestedInvocationId
  );
  const requestedInvocation = useMemo(() => {
    if (!requestedInvocationQueryData)
      return invocations?.find((i) => i.id === requestedInvocationId);
    else return requestedInvocationQueryData;
  }, [requestedInvocationQueryData, invocations, requestedInvocationId]);

  useEffect(() => {
    setSelectedTrace(requestedInvocation);
  }, [requestedInvocation]);

  const handleCopyCode = () => {
    const fullCode = `${lmp?.dependencies.trim()}\n\n${lmp?.source.trim()}`;
    navigator.clipboard
      .writeText(fullCode)
      .then(() => {
        toast.success("Code copied to clipboard", {
          duration: 2000,
          position: "top-center",
        });
      })
      .catch((err) => {
        console.error("Failed to copy code: ", err);
        toast.error("Failed to copy code", {
          duration: 2000,
          position: "top-center",
        });
      });
  };

  const handleViewModeToggle = () => {
    setViewMode((prevMode) => (prevMode === "Source" ? "Diff" : "Source"));
  };

  if (isLoadingLMP)
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900 text-gray-100">
        Loading...
      </div>
    );

  const omitColumns = ["name"];

  return (
    <ResizablePanelGroup
      direction="horizontal"
      className="w-full h-screen"
    >
      <ResizablePanel defaultSize={selectedTrace ? 100 : 70} minSize={30}>
        {/* <ScrollArea className="h-full"> */}
          <InvocationsLayout
            selectedTrace={selectedTrace}
            setSelectedTrace={setSelectedTrace}
            showSidebar={true}
          >
            <header className="bg-[#1c1f26] p-4 flex justify-between items-center">
              <h1 className="text-lg font-semibold">
                <Link to={`/lmp/${lmp?.name}`}>
                  <LMPCardTitle lmp={lmp} />
                </Link>
              </h1>
              <div className="flex space-x-2">
                <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-sm hover:bg-[#3a3f4b] transition-colors">
                  Add to Dataset
                </button>
                <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-sm hover:bg-[#3a3f4b] transition-colors">
                  Share
                </button>
              </div>
            </header>

            <main className="p-6 overflow-y-auto hide-scrollbar">
              <div className="mb-6 bg-[#1c1f26] rounded-lg p-4">
                <div className="flex justify-between items-center mb-4">
                  <div className="flex items-center space-x-4">
                    <h2 className="text-md font-semibold">
                      Language Model Program
                    </h2>
                    {(id || requestedInvocationId) && (
                      <>
                        <span className="text-gray-500 mx-2">•</span>
                        <VersionBadge
                          version={
                            id
                              ? lmp?.version_number + 1
                              : requestedInvocation?.lmp.version_number + 1
                          }
                          hash={id ? lmp?.lmp_id : requestedInvocation?.lmp_id}
                        />
                      </>
                    )}
                  </div>
                  <div className="flex space-x-4 items-center">
                    {previousVersion && (
                      <>
                        {viewMode === "Diff" && (
                          <div className="flex items-center text-sm text-gray-400">
                            <FiGitCommit className="mr-2" />
                            <span className="mr-2">Comparing to </span>
                            <VersionBadge
                              version={previousVersion.version_number + 1}
                              hash={previousVersion.lmp_id}
                              className="opacity-40 "
                            />
                          </div>
                        )}
                        <ToggleSwitch
                          leftLabel="Source"
                          rightLabel="Diff"
                          isRight={viewMode === "Diff"}
                          onToggle={handleViewModeToggle}
                        />
                      </>
                    )}
                    <button
                      className="p-1 rounded bg-[#2a2f3a] hover:bg-[#3a3f4b] transition-colors"
                      onClick={handleCopyCode}
                    >
                      <FiCopy className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div className="overflow-hidden">
                  <LMPSourceView
                    lmp={lmp}
                    selectedInvocation={selectedTrace}
                    showDependenciesInitial={!!id}
                    previousVersion={previousVersion}
                    viewMode={previousVersion ? viewMode : "Source"}
                  />
                </div>
              </div>

              <div className="mb-6">
                <div className="flex border-b border-gray-700">
                  {["Runs", "Version History", "Dependency Graph"].map(
                    (tab) => (
                      <button
                        key={tab}
                        className={`px-4 py-2 focus:outline-none ${
                          activeTab === tab.toLowerCase().replace(" ", "_")
                            ? "text-blue-400 border-b-2 border-blue-400 font-medium"
                            : "text-gray-400 hover:text-gray-200"
                        }`}
                        onClick={() =>
                          setActiveTab(tab.toLowerCase().replace(" ", "_"))
                        }
                      >
                        {tab}
                      </button>
                    )
                  )}
                </div>

                <div className="mt-4">
                  {activeTab === "runs" && (
                    <>
                      <div className="flex justify-between items-center mb-4">
                        <div className="flex space-x-2">
                          <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-xs hover:bg-[#3a3f4b] transition-colors flex items-center">
                            <FiFilter className="mr-1" /> 1 filter
                          </button>
                          <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-xs hover:bg-[#3a3f4b] transition-colors">
                            Last 7 days
                          </button>
                          <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-xs hover:bg-[#3a3f4b] transition-colors">
                            Root Runs
                          </button>
                          <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-xs hover:bg-[#3a3f4b] transition-colors">
                            LLM Calls
                          </button>
                          <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-xs hover:bg-[#3a3f4b] transition-colors">
                            All Runs
                          </button>
                        </div>
                        <button className="p-1 rounded bg-[#2a2f3a] hover:bg-[#3a3f4b] transition-colors">
                          <FiColumns className="w-4 h-4" />
                        </button>
                      </div>
                      <InvocationsTable
                        invocations={invocations}
                        currentPage={currentPage}
                        pageSize={pageSize}
                        setCurrentPage={setCurrentPage}
                        producingLmp={lmp}
                        onSelectTrace={(trace) => {
                          setSelectedTrace(trace);
                          setSearchParams({ i: trace.id });
                        }}
                        currentlySelectedTrace={selectedTrace}
                        omitColumns={omitColumns}
                      />
                    </>
                  )}
                  {activeTab === "version_history" && (
                    <VersionHistoryPane versions={versionHistory} />
                  )}
                  {activeTab === "dependency_graph" && !!uses && (
                    <DependencyGraphPane
                      key={uses
                        ?.map((lmp) => lmp.lmp_id)
                        .sort()
                        .join("-")}
                      lmp={lmp}
                      uses={uses}
                    />
                  )}
                </div>
              </div>
            </main>
          </InvocationsLayout>
        {/* </ScrollArea> */}
      </ResizablePanel>
      {!selectedTrace && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={30} minSize={20}>
            <LMPDetailsSidePanel
              lmp={lmp}
              uses={uses}
              versionHistory={versionHistory}
            />
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  );
}

export default LMP;
