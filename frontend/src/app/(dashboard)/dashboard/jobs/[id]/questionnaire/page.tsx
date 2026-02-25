"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import {
  addQuestion,
  deleteQuestion,
  getJob,
  reorderQuestions,
  updateQuestion,
} from "@/lib/jobsAPI";
import type { Job, JobQuestion, JobQuestionCreate, QuestionType } from "@/types/job";

const QUESTION_TYPES: Array<{ value: QuestionType; label: string }> = [
  { value: "text", label: "Text" },
  { value: "yes_no", label: "Yes / No" },
  { value: "multiple_choice", label: "Multiple Choice" },
  { value: "rating", label: "Rating (1–5)" },
];

export default function QuestionnairePage() {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [questions, setQuestions] = useState<JobQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New question form
  const [newQ, setNewQ] = useState<JobQuestionCreate>({
    question_text: "",
    question_type: "text",
    is_required: true,
  });
  const [newOptions, setNewOptions] = useState<string[]>(["", ""]);

  // Edit state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [editType, setEditType] = useState<QuestionType>("text");
  const [editOptions, setEditOptions] = useState<string[]>([]);
  const [editRequired, setEditRequired] = useState(true);

  // Drag
  const [dragId, setDragId] = useState<string | null>(null);

  useEffect(() => {
    getJob(id)
      .then((j) => {
        setJob(j);
        setQuestions([...j.questions].sort((a, b) => a.display_order - b.display_order));
      })
      .catch(() => setError("Failed to load questionnaire."))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleAdd() {
    if (!newQ.question_text.trim()) return;
    const data: JobQuestionCreate = {
      ...newQ,
      options:
        newQ.question_type === "multiple_choice"
          ? newOptions.filter((o) => o.trim())
          : undefined,
    };
    const q = await addQuestion(id, data);
    setQuestions((prev) => [...prev, q]);
    setNewQ({ question_text: "", question_type: "text", is_required: true });
    setNewOptions(["", ""]);
  }

  async function handleDelete(qId: string) {
    await deleteQuestion(id, qId);
    setQuestions((prev) => prev.filter((q) => q.id !== qId));
  }

  function startEdit(q: JobQuestion) {
    setEditingId(q.id);
    setEditText(q.question_text);
    setEditType(q.question_type);
    setEditOptions(q.options ?? ["", ""]);
    setEditRequired(q.is_required);
  }

  async function saveEdit(qId: string) {
    const updated = await updateQuestion(id, qId, {
      question_text: editText,
      question_type: editType,
      options: editType === "multiple_choice" ? editOptions.filter((o) => o.trim()) : undefined,
      is_required: editRequired,
    });
    setQuestions((prev) => prev.map((q) => (q.id === qId ? updated : q)));
    setEditingId(null);
  }

  function onDrop(targetId: string) {
    if (!dragId || dragId === targetId) return;
    const reordered = [...questions];
    const from = reordered.findIndex((q) => q.id === dragId);
    const to = reordered.findIndex((q) => q.id === targetId);
    const moved = reordered.splice(from, 1)[0]!;
    reordered.splice(to, 0, moved);
    const withOrder = reordered.map((q, i) => ({ ...q, display_order: i }));
    setQuestions(withOrder);
    reorderQuestions(id, withOrder.map((q) => q.id));
    setDragId(null);
  }

  if (loading) return <div className="p-8 text-gray-500">Loading…</div>;
  if (error || !job)
    return <div className="p-8 text-red-600">{error ?? "Not found"}</div>;

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Screening Questions</h1>
        <p className="text-sm text-gray-500 mt-1">{job.title}</p>
      </div>

      {/* Question list */}
      <div className="space-y-3 mb-6">
        {questions.length === 0 && (
          <p className="text-gray-500 text-sm">No questions yet. Add one below.</p>
        )}
        {questions.map((q, idx) => (
          <div
            key={q.id}
            draggable
            onDragStart={() => setDragId(q.id)}
            onDragOver={(e) => e.preventDefault()}
            onDrop={() => onDrop(q.id)}
            className="bg-white border border-gray-200 rounded-xl px-4 py-3"
          >
            {editingId === q.id ? (
              <div className="space-y-3">
                <input
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
                />
                <div className="flex items-center gap-3">
                  <select
                    value={editType}
                    onChange={(e) => setEditType(e.target.value as QuestionType)}
                    className="px-2 py-1.5 text-sm border border-gray-300 rounded-lg"
                  >
                    {QUESTION_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
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
                  <div className="space-y-1">
                    {editOptions.map((opt, i) => (
                      <input
                        key={i}
                        value={opt}
                        onChange={(e) => {
                          const updated = [...editOptions];
                          updated[i] = e.target.value;
                          setEditOptions(updated);
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
                  <button onClick={() => saveEdit(q.id)} className="px-3 py-1 text-xs bg-indigo-600 text-white rounded-lg">
                    Save
                  </button>
                  <button onClick={() => setEditingId(null)} className="px-3 py-1 text-xs text-gray-600">
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-2">
                  <span className="text-gray-300 cursor-grab mt-0.5">⠿</span>
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      {idx + 1}. {q.question_text}
                      {q.is_required && <span className="text-red-500 ml-1">*</span>}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {QUESTION_TYPES.find((t) => t.value === q.question_type)?.label}
                      {q.options && q.options.length > 0 && (
                        <span className="ml-1">— {q.options.join(", ")}</span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button onClick={() => startEdit(q)} className="text-xs text-gray-500 hover:text-indigo-600">
                    Edit
                  </button>
                  <button onClick={() => handleDelete(q.id)} className="text-xs text-red-500 hover:text-red-700">
                    Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add question */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">Add Question</h2>

        <div>
          <label className="block text-xs text-gray-600 mb-1">Question text</label>
          <input
            value={newQ.question_text}
            onChange={(e) => setNewQ((p) => ({ ...p, question_text: e.target.value }))}
            placeholder="e.g. Do you have experience with TypeScript?"
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>

        <div className="flex items-center gap-3">
          <select
            value={newQ.question_type}
            onChange={(e) =>
              setNewQ((p) => ({ ...p, question_type: e.target.value as QuestionType }))
            }
            className="px-2 py-1.5 text-sm border border-gray-300 rounded-lg"
          >
            {QUESTION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <label className="flex items-center gap-1.5 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={newQ.is_required}
              onChange={(e) => setNewQ((p) => ({ ...p, is_required: e.target.checked }))}
            />
            Required
          </label>
        </div>

        {newQ.question_type === "multiple_choice" && (
          <div className="space-y-1.5">
            {newOptions.map((opt, i) => (
              <input
                key={i}
                value={opt}
                onChange={(e) => {
                  const updated = [...newOptions];
                  updated[i] = e.target.value;
                  setNewOptions(updated);
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
          className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
        >
          Add Question
        </button>
      </div>
    </div>
  );
}
