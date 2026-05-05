import { ArrowRight, CheckCircle2, CircleDot, ShieldCheck } from 'lucide-react'

const pathStages = [
  {
    title: 'Lead capture',
    owner: 'Public sensing surface',
    copy: 'A prospect uses sensing tools and requests follow-up with market, readiness, benchmark, or credit-spread context preserved as screening evidence.',
  },
  {
    title: 'Pilot qualification',
    owner: 'Muni-Pal operator review',
    copy: 'The lead is reviewed for sector fit, contact quality, baseline facts, and advisor coverage before any BFMS project exists.',
  },
  {
    title: 'BFMS project creation',
    owner: 'Authenticated BFMS user',
    copy: 'Only a qualified lead can be converted into a BFMS project, carrying forward issuer context, sector playbook, and a durable conversion event.',
  },
  {
    title: 'Pilot onboarding',
    owner: 'Pilot onboarding workflow',
    copy: 'The project enters intake, document request, upload, extraction, review, readiness, and advisor-ready handoff stages.',
  },
]

const gates = [
  'Registered MA confirmed',
  'Pilot smoke test green',
  'Engagement scope signed',
]

const sectorPosture = [
  'Healthcare is the primary launch pilot path, with the deepest readiness and handoff expectations.',
  'Housing is pilot-stage and should be framed as a controlled secondary walkthrough, not mature automation.',
  'UCS/WTE remains supported as a control sector and should not be dropped from the platform model.',
]

const boundaries = [
  'This is not deal approval.',
  'This is not municipal advisory advice.',
  'This is not legal advice, bond sizing, pricing recommendation, or issuance instruction.',
]

export default function PilotNavigation() {
  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="h-12 w-12 rounded-lg bg-indigo-600 flex items-center justify-center">
            <CircleDot className="h-6 w-6 text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-primary-600">
              Sensing to pilot bridge
            </p>
            <h1 className="text-3xl font-bold text-gray-900">Pilot Navigation</h1>
          </div>
        </div>
        <p className="text-gray-600 leading-relaxed max-w-3xl">
          Pilot Navigation explains how a public sensing lead can move from
          lead capture to pilot qualification, BFMS project creation, and pilot
          onboarding without turning public tooling into an approval engine or
          admin shortcut.
        </p>
      </div>

      <section className="grid gap-4 md:grid-cols-4">
        {pathStages.map((stage, index) => (
          <article
            key={stage.title}
            className="bg-white rounded-lg border border-gray-200 shadow-sm p-5"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold text-primary-600 uppercase tracking-wide">
                Step {index + 1}
              </span>
              {index < pathStages.length - 1 && (
                <ArrowRight className="h-4 w-4 text-gray-300" />
              )}
            </div>
            <h2 className="text-lg font-semibold text-gray-900">{stage.title}</h2>
            <p className="text-xs font-medium text-gray-500 mt-1">{stage.owner}</p>
            <p className="text-sm text-gray-600 mt-3 leading-relaxed">{stage.copy}</p>
          </article>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Pre-pilot gates</h2>
          <ul className="space-y-3">
            {gates.map((gate) => (
              <li key={gate} className="flex items-start gap-3 text-sm text-gray-700">
                <CheckCircle2 className="h-5 w-5 text-emerald-600 mt-0.5" />
                <span>{gate}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Sector posture</h2>
          <ul className="space-y-3 text-sm text-gray-700 leading-relaxed">
            {sectorPosture.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="bg-white rounded-lg border border-amber-200 bg-amber-50 shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck className="h-5 w-5 text-amber-700" />
            <h2 className="text-lg font-semibold text-gray-900">Compliance boundary</h2>
          </div>
          <ul className="space-y-3 text-sm text-gray-800 leading-relaxed">
            {boundaries.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  )
}
