"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import {
  addPipelineStage,
  deletePipelineStage,
  getJob,
  reorderPipeline,
  updatePipelineStage,
} from "@/lib/jobsAPI";
import type { Job, PipelineStage, PipelineStageReorderItem } from "@/types/job";

export default function PipelinePage() {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newStageName, setNewStageName] = useState("");
  const [newStageColor, setNewStageColor] = useState("#6366f1");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editColor, setEditColor] = useState("");
  const [dragOver, setDragOver] = useState<string | null>(null);

  useEffect(() => {
    getJob(id)
      .then((j) => {
        setJob(j);
        setStages([...j.pipeline_stages].sort((a, b) => a.stage_order - b.stage_order));
      })
      .catch(() => setError("Failed to load pipeline."))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleAdd() {
    if (!newStageName.trim()) return;
    const stage = await addPipelineStage(id, {
      stage_name: newStageName.trim(),
      color: newStageColor,
    });
    setStages((prev) => [...prev, stage]);
    setNewStageName("");
    setNewStageColor("#6366f1");
  }

  async function handleDelete(stageId: string) {
    if (!confirm("Delete this stage?")) return;
    await deletePipelineStage(id, stageId);
    setStages((prev) => prev.filter((s) => s.id !== stageId));
  }

  function startEdit(stage: PipelineStage) {
    setEditingId(stage.id);
    setEditName(stage.stage_name);
    setEditColor(stage.color);
  }

  async function saveEdit(stageId: string) {
    const updated = await updatePipelineStage(id, stageId, {
      stage_name: editName,
      color: editColor,
    });
    setStages((prev) =>
      prev.map((s) => (s.id === stageId ? updated : s))
    );
    setEditingId(null);
  }

  // Drag-and-drop (native HTML5 — no extra library needed for a simple list)
  const [dragId, setDragId] = useState<string | null>(null);

  function onDragStart(stageId: string) {
    setDragId(stageId);
  }

  function onDrop(targetId: string) {
    if (!dragId || dragId === targetId) return;

    const reordered = [...stages];
    const from = reordered.findIndex((s) => s.id === dragId);
    const to = reordered.findIndex((s) => s.id === targetId);
    const moved = reordered.splice(from, 1)[0]!;
    reordered.splice(to, 0, moved);

    const withOrder = reordered.map((s, i) => ({ ...s, stage_order: i }));
    setStages(withOrder);

    const items: PipelineStageReorderItem[] = withOrder.map((s) => ({
      id: s.id,
      stage_order: s.stage_order,
    }));
    reorderPipeline(id, items);
    setDragId(null);
    setDragOver(null);
  }

  if (loading) return <div className="p-8 text-gray-500">Loading…</div>;
  if (error || !job)
    return <div className="p-8 text-red-600">{error ?? "Not found"}</div>;

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Hiring Pipeline</h1>
        <p className="text-sm text-gray-500 mt-1">{job.title}</p>
      </div>

      {/* Stage list */}
      <div className="space-y-2 mb-6">
        {stages.map((stage) => (
          <div
            key={stage.id}
            draggable
            onDragStart={() => onDragStart(stage.id)}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(stage.id);
            }}
            onDrop={() => onDrop(stage.id)}
            onDragLeave={() => setDragOver(null)}
            className={`flex items-center gap-3 bg-white border rounded-xl px-4 py-3 cursor-grab transition-all ${
              dragOver === stage.id
                ? "border-indigo-400 shadow-md"
                : "border-gray-200"
            }`}
          >
            {/* Drag handle */}
            <span className="text-gray-300 cursor-grab">⠿</span>

            {/* Color swatch */}
            <div
              className="w-4 h-4 rounded-full flex-shrink-0"
              style={{ backgroundColor: stage.color }}
            />

            {/* Name / edit */}
            {editingId === stage.id ? (
              <div className="flex-1 flex items-center gap-2">
                <input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
                />
                <input
                  type="color"
                  value={editColor}
                  onChange={(e) => setEditColor(e.target.value)}
                  className="w-8 h-8 rounded border border-gray-300 cursor-pointer p-0.5"
                />
                <button
                  onClick={() => saveEdit(stage.id)}
                  className="px-2 py-1 text-xs bg-indigo-600 text-white rounded-lg"
                >
                  Save
                </button>
                <button
                  onClick={() => setEditingId(null)}
                  className="px-2 py-1 text-xs text-gray-600 hover:text-gray-900"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-between">
                <span className="text-sm font-medium text-gray-800">
                  {stage.stage_name}
                  {stage.is_default && (
                    <span className="ml-2 text-xs text-gray-400 font-normal">
                      (default)
                    </span>
                  )}
                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => startEdit(stage)}
                    className="px-2 py-1 text-xs text-gray-500 hover:text-indigo-600"
                  >
                    Edit
                  </button>
                  {!stage.is_default && (
                    <button
                      onClick={() => handleDelete(stage.id)}
                      className="px-2 py-1 text-xs text-red-500 hover:text-red-700"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add stage */}
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Add Stage</h2>
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={newStageName}
            onChange={(e) => setNewStageName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            placeholder="Stage name"
            className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
          <input
            type="color"
            value={newStageColor}
            onChange={(e) => setNewStageColor(e.target.value)}
            className="w-10 h-10 rounded-lg border border-gray-300 cursor-pointer p-0.5"
          />
          <button
            onClick={handleAdd}
            className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
          >
            Add
          </button>
        </div>
      </div>
    </div>
  );
}
