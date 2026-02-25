"use client";

/**
 * QuestionnaireBuilder — reusable drag-and-drop question editor.
 * Can be embedded in any page; manages local state and syncs to API via callbacks.
 */

import { useState } from "react";

import type { JobQuestion, JobQuestionCreate, QuestionType } from "@/types/job";

const QUESTION_TYPES: Array<{ value: QuestionType; label: string }> = [
  { value: "text", label: "Text" },
  { value: "yes_no", label: "Yes / No" },
  { value: "multiple_choice", label: "Multiple Choice" },
  { value: "rating", label: "Rating (1–5)" },
];

interface QuestionnaireBuilderProps {
  questions: JobQuestion[];
  onAdd: (data: JobQuestionCreate) => Promise<void>;
  onUpdate: (id: string, data: Partial<JobQuestionCreate>) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onReorder: (ids: string[]) => Promise<void>;
}

export function QuestionnaireBuilder({
  questions,
  onAdd,
  onUpdate,
  onDelete,
  onReorder,
}: QuestionnaireBuilderProps) {
  const [items, setItems] = useState<JobQuestion[]>(
    [...questions].sort((a, b) => a.display_order - b.display_order)
  );

  // New question state
  const [newText, setNewText] = useState("");
  const [newType, setNewType] = useState<QuestionType>("text");
  const [newRequired, setNewRequired] = useState(true);
  const [newOptions, setNewOptions] = useState<string[]>(["", ""]);
  const [adding, setAdding] = useState(false);

  // Edit state
  const [editId, setEditId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [editType, setEditType] = useState<QuestionType>("text");
  const [editRequired, setEditRequired] = useState(true);
  const [editOptions, setEditOptions] = useState<string[]>([]);

  // Drag state
  const [dragId, setDragId] = useState<string | null>(null);

  async function handleAdd() {
    if (!newText.trim()) return;
    setAdding(true);
    try {
      await onAdd({
        question_text: newText.trim(),
        question_type: newType,
        is_required: newRequired,
        options:
          newType === "multiple_choice"
            ? newOptions.filter((o) => o.trim())
            : undefined,
      });
      setNewText("");
      setNewType("text");
      setNewRequired(true);
      setNewOptions(["", ""]);
    } finally {
      setAdding(false);
    }
  }

  function startEdit(q: JobQuestion) {
    setEditId(q.id);
    setEditText(q.question_text);
    setEditType(q.question_type);
    setEditRequired(q.is_required);
    setEditOptions(q.options ?? ["", ""]);
  }

  async function saveEdit() {
    if (!editId) return;
    await onUpdate(editId, {
      question_text: editText,
      question_type: editType,
      is_required: editRequired,
      options:
        editType === "multiple_choice"
          ? editOptions.filter((o) => o.trim())
          : undefined,
    });
    setEditId(null);
  }

  function onDrop(targetId: string) {
    if (!dragId || dragId === targetId) return;
    const reordered = [...items];
    const fromIdx = reordered.findIndex((q) => q.id === dragId);
    const toIdx = reordered.findIndex((q) => q.id === targetId);
    const moved = reordered.splice(fromIdx, 1)[0]!;
    reordered.splice(toIdx, 0, moved);
    setItems(reordered);
    onReorder(reordered.map((q) => q.id));
    setDragId(null);
  }

  return (
    <div className="space-y-4">
      {/* Question list */}
      <div className="space-y-2">
        {items.map((q, idx) => (
          <div
            key={q.id}
            draggable
            onDragStart={() => setDragId(q.id)}
            onDragOver={(e) => e.preventDefault()}
            onDrop={() => onDrop(q.id)}
            className="bg-white border border-gray-200 rounded-xl px-4 py-3"
          >
            {editId === q.id ? (
              <div className="space-y-3">
                <input
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
                />
                <div className="flex items-center gap-3 flex-wrap">
                  <select
                    value={editType}
                    onChange={(e) => setEditType(e.target.value as QuestionType)}
                    className="px-2 py-1.5 text-sm border border-gray-300 rounded-lg"
                  >
                    {QUESTION_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                  <label className="flex items-center gap-1.5 text-sm text-gray-600">
                    <input
                      type="checkbox"
                      checked={editRequired}
                      onChange={(e) => setEditRequired(e.target.checked)}
                    />
                    Required
                  </label>
                </div>
                {editType === "multiple_choice" && (
                  <div className="space-y-1.5 pl-2">
                    {editOptions.map((opt, i) => (
                      <input
                        key={i}
                        value={opt}
                        onChange={(e) => {
                          const upd = [...editOptions];
                          upd[i] = e.target.value;
                          setEditOptions(upd);
                        }}
                        placeholder={`Option ${i + 1}`}
                        className="w-full px-2 py-1 text-sm border border-gray-200 rounded-lg"
                      />
                    ))}
                    <button
                      onClick={() => setEditOptions((p) => [...p, ""])}
                      className="text-xs text-indigo-600 hover:underline"
                    >
                      + Add option
                    </button>
                  </div>
                )}
                <div className="flex gap-2">
                  <button
                    onClick={saveEdit}
                    className="px-3 py-1 text-xs bg-indigo-600 text-white rounded-lg"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => setEditId(null)}
                    className="px-3 py-1 text-xs text-gray-600"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-2">
                  <span className="text-gray-300 cursor-grab mt-0.5 select-none">
                    ⠿
                  </span>
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      {idx + 1}. {q.question_text}
                      {q.is_required && (
                        <span className="text-red-500 ml-1">*</span>
                      )}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {QUESTION_TYPES.find((t) => t.value === q.question_type)
                        ?.label ?? q.question_type}
                      {q.options && q.options.length > 0 && (
                        <span className="ml-1">
                          — {q.options.join(", ")}
                        </span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => startEdit(q)}
                    className="text-xs text-gray-500 hover:text-indigo-600 px-1"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => onDelete(q.id)}
                    className="text-xs text-red-500 hover:text-red-700 px-1"
                  >
                    Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}

        {items.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-6">
            No questions yet. Add one below.
          </p>
        )}
      </div>

      {/* Add question form */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-3">
        <p className="text-sm font-semibold text-gray-700">Add Question</p>
        <input
          value={newText}
          onChange={(e) => setNewText(e.target.value)}
          placeholder="Type your question…"
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={newType}
            onChange={(e) => setNewType(e.target.value as QuestionType)}
            className="px-2 py-1.5 text-sm border border-gray-300 rounded-lg"
          >
            {QUESTION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-1.5 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={newRequired}
              onChange={(e) => setNewRequired(e.target.checked)}
            />
            Required
          </label>
        </div>
        {newType === "multiple_choice" && (
          <div className="space-y-1.5">
            {newOptions.map((opt, i) => (
              <input
                key={i}
                value={opt}
                onChange={(e) => {
                  const upd = [...newOptions];
                  upd[i] = e.target.value;
                  setNewOptions(upd);
                }}
                placeholder={`Option ${i + 1}`}
                className="w-full px-2 py-1 text-sm border border-gray-200 rounded-lg"
              />
            ))}
            <button
              onClick={() => setNewOptions((p) => [...p, ""])}
              className="text-xs text-indigo-600 hover:underline"
            >
              + Add option
            </button>
          </div>
        )}
        <button
          onClick={handleAdd}
          disabled={adding}
          className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium"
        >
          {adding ? "Adding…" : "Add Question"}
        </button>
      </div>
    </div>
  );
}
