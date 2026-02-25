"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Loader2, MapPin, Briefcase, IndianRupee, CheckCircle } from "lucide-react";
import { toast } from "sonner";

import { applicationAPI } from "@/lib/applicationAPI";
import type { JobSearchResult } from "@/types/application";

interface Question {
  id: string;
  question_text: string;
  question_type: string;
  is_required: boolean;
}

function fmt(n: number) {
  return n >= 100000
    ? `₹${(n / 100000).toFixed(1)}L`
    : `₹${(n / 1000).toFixed(0)}K`;
}

export default function ApplyPage() {
  const { id: jobId } = useParams<{ id: string }>();
  const router = useRouter();

  const [job, setJob] = useState<JobSearchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [applied, setApplied] = useState(false);
  const [coverLetter, setCoverLetter] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});

  useEffect(() => {
    applicationAPI
      .getJobDetail(jobId)
      .then(r => {
        setJob(r.data as JobSearchResult);
        // Initialise answers for each question
        const qs: Question[] = (r.data as { questions?: Question[] }).questions || [];
        const init: Record<string, string> = {};
        qs.forEach(q => { init[q.id] = ""; });
        setAnswers(init);
      })
      .catch(() => toast.error("Job not found"))
      .finally(() => setLoading(false));
  }, [jobId]);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const answerList = Object.entries(answers).map(([question_id, answer_text]) => ({
        question_id,
        answer_text: answer_text || undefined,
      }));
      await applicationAPI.apply(jobId, {
        cover_letter: coverLetter || undefined,
        answers: answerList,
      });
      setApplied(true);
      toast.success("Application submitted!");
    } catch (err: unknown) {
      const status = (err as { response?: { status: number } })?.response?.status;
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      if (status === 409) {
        toast.error("You have already applied to this job.");
      } else {
        toast.error(detail || "Failed to submit application");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
    </div>
  );

  if (!job) return (
    <div className="text-center py-20 text-gray-400">
      <p>Job not found or no longer active.</p>
      <button onClick={() => router.back()} className="mt-4 text-indigo-600 hover:underline text-sm">Go back</button>
    </div>
  );

  if (applied) return (
    <div className="max-w-xl mx-auto text-center py-20">
      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <CheckCircle className="w-8 h-8 text-green-600" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Application Submitted!</h2>
      <p className="text-gray-500 mb-6">
        Your application for <strong>{job.title}</strong> at <strong>{job.company_name}</strong> has been sent.
      </p>
      <div className="flex items-center justify-center gap-3">
        <button
          onClick={() => router.push("/dashboard/my-applications")}
          className="bg-indigo-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-700"
        >
          Track Applications
        </button>
        <button
          onClick={() => router.push("/dashboard/browse-jobs")}
          className="border border-gray-200 text-gray-700 px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-gray-50"
        >
          Browse More Jobs
        </button>
      </div>
    </div>
  );

  const questions: Question[] = (job as { questions?: Question[] }).questions || [];

  return (
    <div className="max-w-2xl pb-12">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 mb-5"
      >
        <ArrowLeft className="w-4 h-4" /> Back to jobs
      </button>

      {/* Job summary */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-5">
        <h1 className="text-xl font-bold text-gray-900">{job.title}</h1>
        <p className="text-gray-600 mt-0.5">{job.company_name}</p>
        <div className="flex flex-wrap gap-3 mt-3 text-sm text-gray-500">
          {job.location && (
            <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {job.location}</span>
          )}
          {job.job_type && (
            <span className="flex items-center gap-1 capitalize"><Briefcase className="w-3.5 h-3.5" /> {job.job_type.replace("_", " ")}</span>
          )}
          {(job.salary_min || job.salary_max) && (
            <span className="flex items-center gap-1">
              <IndianRupee className="w-3.5 h-3.5" />
              {job.salary_min ? fmt(job.salary_min) : "?"} – {job.salary_max ? fmt(job.salary_max) : "?"}
            </span>
          )}
        </div>
        {job.description && (
          <p className="text-sm text-gray-600 mt-3 line-clamp-3">{job.description}</p>
        )}
      </div>

      {/* Application form */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-5">
        <h2 className="font-semibold text-gray-900">Your Application</h2>

        {/* Cover letter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Cover Letter <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <textarea
            rows={5}
            value={coverLetter}
            onChange={e => setCoverLetter(e.target.value)}
            placeholder="Tell the hiring team why you're a great fit for this role..."
            className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>

        {/* Questionnaire */}
        {questions.length > 0 && (
          <div className="space-y-4">
            <p className="text-sm font-medium text-gray-700">Screening Questions</p>
            {questions.map((q, idx) => (
              <div key={q.id}>
                <label className="block text-sm text-gray-700 mb-1.5">
                  {idx + 1}. {q.question_text}
                  {q.is_required && <span className="text-red-500 ml-1">*</span>}
                </label>
                {q.question_type === "textarea" ? (
                  <textarea
                    rows={3}
                    value={answers[q.id] || ""}
                    onChange={e => setAnswers(a => ({ ...a, [q.id]: e.target.value }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  />
                ) : (
                  <input
                    type={q.question_type === "number" ? "number" : "text"}
                    value={answers[q.id] || ""}
                    onChange={e => setAnswers(a => ({ ...a, [q.id]: e.target.value }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  />
                )}
              </div>
            ))}
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-lg font-semibold transition-colors disabled:opacity-60"
        >
          {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
          {submitting ? "Submitting…" : "Submit Application"}
        </button>
      </div>
    </div>
  );
}
