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
import { Card } from "../components/common/Card";

import GenericPageLayout from "../components/layouts/GenericPageLayout";

const lmpConfig = {
  getPath: (version) => `/lmp/${version.name}/${version.lmp_id}`,
  getId: (version) => version.lmp_id,
  isCurrentVersion: (version, location) => location.pathname.includes(version.lmp_id)
};

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
    pageSize,
    true // dangerous hierarchical query that will not scale to unique invocations
  );
  const uses = lmp?.uses;

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

  console.log(requestedInvocationId)
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

  const sidebar = useMemo(
    () => (
      <LMPDetailsSidePanel
        lmp={lmp}
        uses={uses}
        versionHistory={versionHistory}
      />
    ),
    [lmp, uses, versionHistory]
  );
  const handleViewModeToggle = () => {
    setViewMode((prevMode) => (prevMode === "Source" ? "Diff" : "Source"));
  };

  if (isLoadingLMP)
    return (
      <div className="flex items-center justify-center h-screen bg-card text-card-foreground">
        Loading...
      </div>
    );

  const omitColumns = ["name"];

  return (
    <GenericPageLayout
      selectedTrace={selectedTrace}
      setSelectedTrace={setSelectedTrace}
      sidebarContent={sidebar}
    >
      <div className="bg-background text-foreground">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-lg flex items-center">
            <Link to={`/lmp/${lmp?.name}`}>
              <Card className="bg-card text-card-foreground">
                <LMPCardTitle lmp={lmp} />
              </Card>
            </Link>
          </h1>
        </div>

        <main className="overflow-y-auto hide-scrollbar">
          <div className="mb-6 bg-card rounded-lg p-4">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center space-x-4">
                <h2 className="text-md font-semibold text-card-foreground">Language Model Program</h2>
                {(id || requestedInvocationId) && (
                  <>
                    <span className="text-muted-foreground mx-2">•</span>
                    <VersionBadge
                      version={
                        id
                          ? lmp?.version_number + 1
                          : requestedInvocation?.lmp.version_number + 1
                      }
                    />
                  </>
                )}
              </div>
              <div className="flex space-x-4 items-center">
                {previousVersion && (
                  <>
                    {viewMode === "Diff" && (
                      <div className="flex items-center text-sm text-muted-foreground">
                        <FiGitCommit className="mr-2" />
                        <span className="mr-2">Comparing to </span>
                        <VersionBadge
                          version={previousVersion.version_number + 1}
                          hash={previousVersion.lmp_id}
                          className="opacity-40"
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
                  className="p-1 rounded bg-secondary hover:bg-secondary/80 transition-colors"
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
            <div className="flex border-b border-border">
              {["Runs", "Version History"].map((tab) => (
                <button
                  key={tab}
                  className={`px-4 py-2 focus:outline-none ${
                    activeTab === tab.toLowerCase().replace(" ", "_")
                      ? "text-primary border-b-2 border-primary font-medium"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                  onClick={() =>
                    setActiveTab(tab.toLowerCase().replace(" ", "_"))
                  }
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="mt-4">
              {activeTab === "runs" && (
                <>
                  <InvocationsTable
                    invocations={invocations}
                    currentPage={currentPage}
                    pageSize={pageSize}
                    setCurrentPage={setCurrentPage}
                    producingLmp={lmp}
                    onSelectTrace={(trace) => {
                      setSelectedTrace(trace);
                      setSearchParams(trace ? { i: trace.id } : {});
                    }}
                    currentlySelectedTrace={selectedTrace}
                    omitColumns={omitColumns}
                  />
                </>
              )}
              {activeTab === "version_history" && (
                <VersionHistoryPane 
                  versions={versionHistory} 
                  config={lmpConfig}
                />
              )}
            </div>
          </div>
        </main>
      </div>
    </GenericPageLayout>
  );
}

export default LMP;
