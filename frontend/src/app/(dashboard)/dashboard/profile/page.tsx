"use client";

import { useEffect, useState, useRef } from "react";
import { toast } from "sonner";
import {
  Briefcase, GraduationCap, Award, FolderOpen, Zap,
  Plus, Trash2, Upload, CheckCircle, ChevronDown, ChevronUp, Download
} from "lucide-react";

import { candidateAPI } from "@/lib/candidateAPI";
import type { CandidateProfile, ProfileStrength } from "@/types/candidate";

// ── Profile strength bar ──────────────────────────────────────────────────────
function StrengthBar({ score }: { score: number }) {
  const color =
    score >= 80 ? "bg-green-500" : score >= 50 ? "bg-amber-500" : "bg-red-500";
  const label =
    score >= 80 ? "Excellent" : score >= 50 ? "Good" : "Needs work";
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-gray-800">Profile Strength</span>
        <span className={`text-sm font-bold ${score >= 80 ? "text-green-600" : score >= 50 ? "text-amber-600" : "text-red-600"}`}>
          {score}/100 · {label}
        </span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-3">
        <div
          className={`h-3 rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

// ── Section wrapper ───────────────────────────────────────────────────────────
function Section({
  title, icon, children, onAdd
}: {
  title: string; icon: React.ReactNode; children: React.ReactNode; onAdd?: () => void
}) {
  const [open, setOpen] = useState(true);
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div
        className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-gray-50"
        onClick={() => setOpen(o => !o)}
      >
        <div className="flex items-center gap-2 font-semibold text-gray-800">
          {icon}
          {title}
        </div>
        <div className="flex items-center gap-2">
          {onAdd && (
            <button
              onClick={e => { e.stopPropagation(); onAdd(); }}
              className="flex items-center gap-1 text-xs bg-indigo-50 text-indigo-600 border border-indigo-200 px-3 py-1.5 rounded-lg hover:bg-indigo-100 transition-colors"
            >
              <Plus className="w-3 h-3" /> Add
            </button>
          )}
          {open ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
        </div>
      </div>
      {open && <div className="px-5 pb-5">{children}</div>}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function ProfilePage() {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [strength, setStrength] = useState<ProfileStrength | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [editingBasic, setEditingBasic] = useState(false);
  const [basicForm, setBasicForm] = useState({
    full_name: "", phone: "", location: "", headline: "", summary: "",
    desired_role: "", desired_salary_min: "", desired_salary_max: "",
    desired_location: "", open_to_remote: true, notice_period_days: "",
    years_of_experience: "",
  });

  // Sub-entity forms
  const [showSkillForm, setShowSkillForm] = useState(false);
  const [skillForm, setSkillForm] = useState({ skill_name: "", proficiency: 3, years_exp: "" });
  const [showExpForm, setShowExpForm] = useState(false);
  const [expForm, setExpForm] = useState({
    company_name: "", job_title: "", employment_type: "full_time",
    location: "", is_current: false, start_date: "", end_date: "", description: ""
  });
  const [showEduForm, setShowEduForm] = useState(false);
  const [eduForm, setEduForm] = useState({
    institution: "", degree: "", field_of_study: "", start_year: "", end_year: "", grade: ""
  });
  const [showCertForm, setShowCertForm] = useState(false);
  const [certForm, setCertForm] = useState({
    name: "", issuing_org: "", issue_date: "", expiry_date: "", credential_id: "", credential_url: ""
  });
  const [showProjectForm, setShowProjectForm] = useState(false);
  const [projectForm, setProjectForm] = useState({
    title: "", description: "", tech_stack: "", project_url: "", repo_url: "", start_date: "", end_date: ""
  });

  const fileRef = useRef<HTMLInputElement>(null);

  const load = async () => {
    try {
      const [p, s] = await Promise.all([
        candidateAPI.getProfile(),
        candidateAPI.getStrength(),
      ]);
      setProfile(p.data);
      setStrength(s.data);
      setBasicForm({
        full_name: p.data.full_name || "",
        phone: p.data.phone || "",
        location: p.data.location || "",
        headline: p.data.headline || "",
        summary: p.data.summary || "",
        desired_role: p.data.desired_role || "",
        desired_salary_min: p.data.desired_salary_min?.toString() || "",
        desired_salary_max: p.data.desired_salary_max?.toString() || "",
        desired_location: p.data.desired_location || "",
        open_to_remote: p.data.open_to_remote,
        notice_period_days: p.data.notice_period_days?.toString() || "",
        years_of_experience: p.data.years_of_experience?.toString() || "",
      });
    } catch {
      toast.error("Failed to load profile");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const saveBasic = async () => {
    try {
      await candidateAPI.updateProfile({
        ...basicForm,
        desired_salary_min: basicForm.desired_salary_min ? Number(basicForm.desired_salary_min) : undefined,
        desired_salary_max: basicForm.desired_salary_max ? Number(basicForm.desired_salary_max) : undefined,
        notice_period_days: basicForm.notice_period_days ? Number(basicForm.notice_period_days) : undefined,
        years_of_experience: basicForm.years_of_experience ? Number(basicForm.years_of_experience) : undefined,
      } as never);
      toast.success("Profile updated!");
      setEditingBasic(false);
      load();
    } catch {
      toast.error("Failed to save profile");
    }
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await candidateAPI.uploadResume(file);
      toast.success("Resume uploaded successfully!");
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || "Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const addSkill = async () => {
    if (!skillForm.skill_name.trim()) return;
    try {
      await candidateAPI.addSkill({
        skill_name: skillForm.skill_name.trim(),
        proficiency: skillForm.proficiency,
        years_exp: skillForm.years_exp ? Number(skillForm.years_exp) : null,
      });
      toast.success("Skill added!");
      setSkillForm({ skill_name: "", proficiency: 3, years_exp: "" });
      setShowSkillForm(false);
      load();
    } catch { toast.error("Failed to add skill"); }
  };

  const deleteSkill = async (id: string) => {
    try {
      await candidateAPI.deleteSkill(id);
      toast.success("Skill removed");
      load();
    } catch { toast.error("Failed to remove skill"); }
  };

  const addExp = async () => {
    if (!expForm.company_name || !expForm.job_title) return;
    try {
      await candidateAPI.addWorkExperience({
        ...expForm,
        start_date: expForm.start_date || null,
        end_date: expForm.end_date || null,
      });
      toast.success("Work experience added!");
      setExpForm({ company_name: "", job_title: "", employment_type: "full_time", location: "", is_current: false, start_date: "", end_date: "", description: "" });
      setShowExpForm(false);
      load();
    } catch { toast.error("Failed to add experience"); }
  };

  const deleteExp = async (id: string) => {
    try { await candidateAPI.deleteWorkExperience(id); toast.success("Removed"); load(); }
    catch { toast.error("Failed"); }
  };

  const addEdu = async () => {
    if (!eduForm.institution) return;
    try {
      await candidateAPI.addEducation({
        institution: eduForm.institution,
        degree: eduForm.degree || null,
        field_of_study: eduForm.field_of_study || null,
        grade: eduForm.grade || null,
        start_year: eduForm.start_year ? Number(eduForm.start_year) : null,
        end_year: eduForm.end_year ? Number(eduForm.end_year) : null,
      });
      toast.success("Education added!");
      setEduForm({ institution: "", degree: "", field_of_study: "", start_year: "", end_year: "", grade: "" });
      setShowEduForm(false);
      load();
    } catch { toast.error("Failed to add education"); }
  };

  const deleteEdu = async (id: string) => {
    try { await candidateAPI.deleteEducation(id); toast.success("Removed"); load(); }
    catch { toast.error("Failed"); }
  };

  const addCert = async () => {
    if (!certForm.name.trim()) return;
    try {
      await candidateAPI.addCertification({
        name: certForm.name.trim(),
        issuing_org: certForm.issuing_org || null,
        issue_date: certForm.issue_date || null,
        expiry_date: certForm.expiry_date || null,
        credential_id: certForm.credential_id || null,
        credential_url: certForm.credential_url || null,
      });
      toast.success("Certification added!");
      setCertForm({ name: "", issuing_org: "", issue_date: "", expiry_date: "", credential_id: "", credential_url: "" });
      setShowCertForm(false);
      load();
    } catch { toast.error("Failed to add certification"); }
  };

  const addProject = async () => {
    if (!projectForm.title.trim()) return;
    try {
      await candidateAPI.addProject({
        title: projectForm.title.trim(),
        description: projectForm.description || null,
        tech_stack: projectForm.tech_stack ? projectForm.tech_stack.split(",").map(s => s.trim()).filter(Boolean) : null,
        project_url: projectForm.project_url || null,
        repo_url: projectForm.repo_url || null,
        start_date: projectForm.start_date || null,
        end_date: projectForm.end_date || null,
      });
      toast.success("Project added!");
      setProjectForm({ title: "", description: "", tech_stack: "", project_url: "", repo_url: "", start_date: "", end_date: "" });
      setShowProjectForm(false);
      load();
    } catch { toast.error("Failed to add project"); }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
    </div>
  );

  const proficiencyLabel = (p: number) =>
    ["", "Beginner", "Elementary", "Intermediate", "Advanced", "Expert"][p] || "";

  return (
    <div className="max-w-3xl space-y-5 pb-12">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
        <p className="text-sm text-gray-500 mt-1">
          A complete profile increases your chances of getting noticed by 3×
        </p>
      </div>

      {/* Strength */}
      {strength && <StrengthBar score={strength.score} />}

      {/* Tips */}
      {strength && strength.tips.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 space-y-1">
          <p className="text-sm font-semibold text-amber-800 mb-1">Quick wins to boost your profile:</p>
          {strength.tips.map((t, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-amber-700">
              <CheckCircle className="w-4 h-4 mt-0.5 shrink-0" />
              {t}
            </div>
          ))}
        </div>
      )}

      {/* Resume */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2">
            <Upload className="w-4 h-4" /> Resume
          </h3>
          <div className="flex items-center gap-2">
            {profile?.resume_url && (
              <a
                href={profile.resume_url}
                download={profile.resume_filename || "resume.pdf"}
                className="flex items-center gap-1.5 text-sm text-indigo-600 border border-indigo-200 px-3 py-2 rounded-lg hover:bg-indigo-50 transition-colors"
              >
                <Download className="w-4 h-4" />
                Download
              </a>
            )}
            <button
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-60"
            >
              {uploading ? "Uploading…" : profile?.resume_filename ? "Replace PDF" : "Upload PDF"}
            </button>
            <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={handleResumeUpload} />
          </div>
        </div>
        {profile?.resume_filename ? (
          <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
            <CheckCircle className="w-4 h-4" />
            {profile.resume_filename}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No resume uploaded yet. PDF only, max 5 MB.</p>
        )}
      </div>

      {/* Basic Info */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-800">Basic Info</h3>
          {editingBasic ? (
            <div className="flex gap-2">
              <button onClick={() => setEditingBasic(false)} className="text-sm px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50">Cancel</button>
              <button onClick={saveBasic} className="text-sm px-3 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700">Save</button>
            </div>
          ) : (
            <button onClick={() => setEditingBasic(true)} className="text-sm px-3 py-1.5 rounded-lg border border-indigo-200 text-indigo-600 hover:bg-indigo-50">Edit</button>
          )}
        </div>
        {editingBasic ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { label: "Full Name", key: "full_name" },
              { label: "Phone", key: "phone" },
              { label: "Location", key: "location" },
              { label: "Headline", key: "headline" },
              { label: "Desired Role", key: "desired_role" },
              { label: "Desired Location", key: "desired_location" },
              { label: "Min Salary (INR)", key: "desired_salary_min" },
              { label: "Max Salary (INR)", key: "desired_salary_max" },
              { label: "Notice Period (days)", key: "notice_period_days" },
              { label: "Years of Experience", key: "years_of_experience" },
            ].map(({ label, key }) => (
              <div key={key}>
                <label className="text-xs text-gray-500 block mb-1">{label}</label>
                <input
                  value={basicForm[key as keyof typeof basicForm] as string}
                  onChange={e => setBasicForm(f => ({ ...f, [key]: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                />
              </div>
            ))}
            <div className="sm:col-span-2">
              <label className="text-xs text-gray-500 block mb-1">Summary</label>
              <textarea
                rows={3}
                value={basicForm.summary}
                onChange={e => setBasicForm(f => ({ ...f, summary: e.target.value }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
          </div>
        ) : (
          <div className="space-y-2 text-sm">
            <div className="grid grid-cols-2 gap-2">
              <div><span className="text-gray-500">Name:</span> <span className="font-medium">{profile?.full_name || "—"}</span></div>
              <div><span className="text-gray-500">Phone:</span> <span className="font-medium">{profile?.phone || "—"}</span></div>
              <div><span className="text-gray-500">Location:</span> <span className="font-medium">{profile?.location || "—"}</span></div>
              <div><span className="text-gray-500">Experience:</span> <span className="font-medium">{profile?.years_of_experience ? `${profile.years_of_experience} yrs` : "—"}</span></div>
            </div>
            {profile?.headline && <p className="text-indigo-700 font-medium">{profile.headline}</p>}
            {profile?.summary && <p className="text-gray-600 text-sm">{profile.summary}</p>}
          </div>
        )}
      </div>

      {/* Skills */}
      <Section title="Skills" icon={<Zap className="w-4 h-4 text-indigo-500" />} onAdd={() => setShowSkillForm(s => !s)}>
        {showSkillForm && (
          <div className="flex flex-wrap gap-2 mb-4 p-3 bg-gray-50 rounded-lg">
            <input
              placeholder="Skill name"
              value={skillForm.skill_name}
              onChange={e => setSkillForm(f => ({ ...f, skill_name: e.target.value }))}
              className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm flex-1 min-w-[140px] focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
            <select
              value={skillForm.proficiency}
              onChange={e => setSkillForm(f => ({ ...f, proficiency: Number(e.target.value) }))}
              className="border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none"
            >
              {[1,2,3,4,5].map(n => <option key={n} value={n}>{n} – {["","Beginner","Elementary","Intermediate","Advanced","Expert"][n]}</option>)}
            </select>
            <input
              placeholder="Yrs exp"
              type="number"
              value={skillForm.years_exp}
              onChange={e => setSkillForm(f => ({ ...f, years_exp: e.target.value }))}
              className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm w-24 focus:outline-none"
            />
            <button onClick={addSkill} className="bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-indigo-700">Add</button>
          </div>
        )}
        {profile?.skills.length === 0 && <p className="text-sm text-gray-400">No skills added yet.</p>}
        <div className="flex flex-wrap gap-2">
          {profile?.skills.map(s => (
            <div key={s.id} className="flex items-center gap-1.5 bg-indigo-50 border border-indigo-200 rounded-full px-3 py-1 text-sm">
              <span className="text-indigo-700 font-medium">{s.skill_name}</span>
              <span className="text-indigo-400 text-xs">· {proficiencyLabel(s.proficiency)}</span>
              <button onClick={() => deleteSkill(s.id)} className="text-red-400 hover:text-red-600 ml-1">
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      </Section>

      {/* Work Experience */}
      <Section title="Work Experience" icon={<Briefcase className="w-4 h-4 text-blue-500" />} onAdd={() => setShowExpForm(s => !s)}>
        {showExpForm && (
          <div className="bg-gray-50 rounded-lg p-4 mb-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">Company *</label>
                <input value={expForm.company_name} onChange={e => setExpForm(f => ({ ...f, company_name: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Job Title *</label>
                <input value={expForm.job_title} onChange={e => setExpForm(f => ({ ...f, job_title: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Start Date</label>
                <input type="date" value={expForm.start_date} onChange={e => setExpForm(f => ({ ...f, start_date: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">End Date</label>
                <input type="date" value={expForm.end_date} onChange={e => setExpForm(f => ({ ...f, end_date: e.target.value }))} disabled={expForm.is_current} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none disabled:bg-gray-100" />
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
              <input type="checkbox" checked={expForm.is_current} onChange={e => setExpForm(f => ({ ...f, is_current: e.target.checked }))} className="rounded" />
              Currently working here
            </label>
            <textarea
              placeholder="Description"
              rows={2}
              value={expForm.description}
              onChange={e => setExpForm(f => ({ ...f, description: e.target.value }))}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none"
            />
            <button onClick={addExp} className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700">Save Experience</button>
          </div>
        )}
        {profile?.work_experiences.length === 0 && <p className="text-sm text-gray-400">No work experience added yet.</p>}
        <div className="space-y-3">
          {profile?.work_experiences.map(exp => (
            <div key={exp.id} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900 text-sm">{exp.job_title}</p>
                <p className="text-gray-600 text-sm">{exp.company_name}{exp.location ? ` · ${exp.location}` : ""}</p>
                <p className="text-gray-400 text-xs mt-0.5">
                  {exp.start_date ? new Date(exp.start_date).toLocaleDateString("en-IN", { month: "short", year: "numeric" }) : ""}
                  {" – "}
                  {exp.is_current ? "Present" : exp.end_date ? new Date(exp.end_date).toLocaleDateString("en-IN", { month: "short", year: "numeric" }) : ""}
                </p>
              </div>
              <button onClick={() => deleteExp(exp.id)} className="text-red-400 hover:text-red-600 p-1">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </Section>

      {/* Education */}
      <Section title="Education" icon={<GraduationCap className="w-4 h-4 text-green-500" />} onAdd={() => setShowEduForm(s => !s)}>
        {showEduForm && (
          <div className="bg-gray-50 rounded-lg p-4 mb-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">Institution *</label>
                <input value={eduForm.institution} onChange={e => setEduForm(f => ({ ...f, institution: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Degree</label>
                <input value={eduForm.degree} onChange={e => setEduForm(f => ({ ...f, degree: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Field of Study</label>
                <input value={eduForm.field_of_study} onChange={e => setEduForm(f => ({ ...f, field_of_study: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Grade / CGPA</label>
                <input value={eduForm.grade} onChange={e => setEduForm(f => ({ ...f, grade: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Start Year</label>
                <input type="number" value={eduForm.start_year} onChange={e => setEduForm(f => ({ ...f, start_year: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">End Year</label>
                <input type="number" value={eduForm.end_year} onChange={e => setEduForm(f => ({ ...f, end_year: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
              </div>
            </div>
            <button onClick={addEdu} className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700">Save Education</button>
          </div>
        )}
        {profile?.educations.length === 0 && <p className="text-sm text-gray-400">No education added yet.</p>}
        <div className="space-y-3">
          {profile?.educations.map(edu => (
            <div key={edu.id} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900 text-sm">{edu.degree}{edu.field_of_study ? ` in ${edu.field_of_study}` : ""}</p>
                <p className="text-gray-600 text-sm">{edu.institution}</p>
                <p className="text-gray-400 text-xs">{edu.start_year && edu.end_year ? `${edu.start_year} – ${edu.end_year}` : ""}{edu.grade ? ` · ${edu.grade}` : ""}</p>
              </div>
              <button onClick={() => deleteEdu(edu.id)} className="text-red-400 hover:text-red-600 p-1">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </Section>

      {/* Certifications */}
      <Section title="Certifications" icon={<Award className="w-4 h-4 text-purple-500" />} onAdd={() => setShowCertForm(s => !s)}>
        {showCertForm && (
          <div className="bg-gray-50 rounded-lg p-4 mb-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="sm:col-span-2">
                <label className="text-xs text-gray-500 block mb-1">Certificate Name *</label>
                <input value={certForm.name} onChange={e => setCertForm(f => ({ ...f, name: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300" placeholder="e.g. AWS Certified Solutions Architect" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Issuing Organization</label>
                <input value={certForm.issuing_org} onChange={e => setCertForm(f => ({ ...f, issuing_org: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" placeholder="e.g. Amazon Web Services" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Credential ID</label>
                <input value={certForm.credential_id} onChange={e => setCertForm(f => ({ ...f, credential_id: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Issue Date</label>
                <input type="date" value={certForm.issue_date} onChange={e => setCertForm(f => ({ ...f, issue_date: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Expiry Date</label>
                <input type="date" value={certForm.expiry_date} onChange={e => setCertForm(f => ({ ...f, expiry_date: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
              </div>
              <div className="sm:col-span-2">
                <label className="text-xs text-gray-500 block mb-1">Credential URL</label>
                <input value={certForm.credential_url} onChange={e => setCertForm(f => ({ ...f, credential_url: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" placeholder="https://..." />
              </div>
            </div>
            <button onClick={addCert} className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700">Save Certification</button>
          </div>
        )}
        {profile?.certifications.length === 0 && !showCertForm && <p className="text-sm text-gray-400">No certifications added yet.</p>}
        <div className="space-y-2">
          {profile?.certifications.map(c => (
            <div key={c.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-sm">{c.name}</p>
                {c.issuing_org && <p className="text-gray-500 text-xs">{c.issuing_org}</p>}
                {(c.issue_date || c.expiry_date) && (
                  <p className="text-gray-400 text-xs mt-0.5">
                    {c.issue_date ? new Date(c.issue_date).toLocaleDateString("en-IN", { month: "short", year: "numeric" }) : ""}
                    {c.expiry_date ? ` – ${new Date(c.expiry_date).toLocaleDateString("en-IN", { month: "short", year: "numeric" })}` : ""}
                  </p>
                )}
                {c.credential_url && (
                  <a href={c.credential_url} target="_blank" rel="noreferrer" className="text-xs text-indigo-500 hover:underline">View credential</a>
                )}
              </div>
              <button onClick={() => candidateAPI.deleteCertification(c.id).then(() => { toast.success("Removed"); load(); })} className="text-red-400 hover:text-red-600 p-1">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </Section>

      {/* Projects */}
      <Section title="Projects" icon={<FolderOpen className="w-4 h-4 text-orange-500" />} onAdd={() => setShowProjectForm(s => !s)}>
        {showProjectForm && (
          <div className="bg-gray-50 rounded-lg p-4 mb-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="sm:col-span-2">
                <label className="text-xs text-gray-500 block mb-1">Project Title *</label>
                <input value={projectForm.title} onChange={e => setProjectForm(f => ({ ...f, title: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300" placeholder="e.g. E-Commerce Platform" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Tech Stack <span className="text-gray-400">(comma separated)</span></label>
                <input value={projectForm.tech_stack} onChange={e => setProjectForm(f => ({ ...f, tech_stack: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" placeholder="React, Node.js, PostgreSQL" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Project URL</label>
                <input value={projectForm.project_url} onChange={e => setProjectForm(f => ({ ...f, project_url: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" placeholder="https://..." />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Repository URL</label>
                <input value={projectForm.repo_url} onChange={e => setProjectForm(f => ({ ...f, repo_url: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" placeholder="https://github.com/..." />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">Start Date</label>
                <input type="date" value={projectForm.start_date} onChange={e => setProjectForm(f => ({ ...f, start_date: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">End Date</label>
                <input type="date" value={projectForm.end_date} onChange={e => setProjectForm(f => ({ ...f, end_date: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" />
              </div>
              <div className="sm:col-span-2">
                <label className="text-xs text-gray-500 block mb-1">Description</label>
                <textarea rows={2} value={projectForm.description} onChange={e => setProjectForm(f => ({ ...f, description: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none" placeholder="What does this project do?" />
              </div>
            </div>
            <button onClick={addProject} className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700">Save Project</button>
          </div>
        )}
        {profile?.projects.length === 0 && !showProjectForm && <p className="text-sm text-gray-400">No projects added yet.</p>}
        <div className="space-y-2">
          {profile?.projects.map(p => (
            <div key={p.id} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm">{p.title}</p>
                {p.description && <p className="text-gray-500 text-xs mt-0.5 line-clamp-2">{p.description}</p>}
                {p.tech_stack && p.tech_stack.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {p.tech_stack.map(t => <span key={t} className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full">{t}</span>)}
                  </div>
                )}
                <div className="flex gap-3 mt-1">
                  {p.project_url && <a href={p.project_url} target="_blank" rel="noreferrer" className="text-xs text-indigo-500 hover:underline">Live</a>}
                  {p.repo_url && <a href={p.repo_url} target="_blank" rel="noreferrer" className="text-xs text-indigo-500 hover:underline">Repo</a>}
                </div>
              </div>
              <button onClick={() => candidateAPI.deleteProject(p.id).then(() => { toast.success("Removed"); load(); })} className="text-red-400 hover:text-red-600 p-1 ml-2 shrink-0">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}
