import React from "react";

export default function App() {
    const stats = [
    { label: "Patients", value: 12 },
    { label: "Coverages", value: 18 },
    { label: "Claims", value: 24 },
    { label: "EDI Exports", value: 7 },
  ];

  const tabs = ["Overview", "Workqueue", "Claim #1", "Eligibility", "Exports", "FHIR Bundle"];
  const [active, setActive] = React.useState("Overview");

  const patient = {
    id: 1,
    first_name: "John",
    last_name: "Doe",
    date_of_birth: "1980-01-01",
    phone: "3125550100",
    email: "john@example.com",
    address: { line: "1 Main", city: "Chicago", state: "IL", postal: "60601" },
  };

  const coverage = {
    id: 1,
    patient: 1,
    payer_name: "Sample Health",
    member_id: "ABC12345",
    group_number: "G123",
    effective_date: "2025-01-01",
    relation_to_subscriber: "self",
    plan: { product: "PPO" },
  };

  const eligibility = {
    snapshot_id: 1,
    payload: {
      active: true,
      network_status: "IN_NETWORK",
      plan: { effective: "2025-01-01", termination: null, group: "SIM123" },
      benefits: [
        { category: "Plan", copay: null, coinsurance: 0.3, deductibleRemaining: 726, authRequired: false },
        { category: "Office Visit", copay: 40, coinsurance: 0.3, deductibleRemaining: 726, authRequired: false },
      ],
      notes: [],
      raw: { mode: "SIMULATED" },
    },
  };

  const claim = {
    id: 1,
    patient_id: 1,
    payer_name: "Sample Health",
    pos: "11",
    total_charge: 150.0,
    diagnoses: [{ order: 1, code: "E11.9" }],
    lines: [
      { id: 10, cpt: "99214", units: 1, charge: 150.0, diagnosis_pointers: [1] },
    ],
    findings: [],
  };

  const workqueue = [
    // Example blocking error rows
    { id: 3, patient_id: 1, payer_name: "Sample Health", pos: "11", total_charge: 200.0, status: "READY", errors: [
      { code: "NCCI_PAIR", message: "99214 conflicts with 99215 (PAIR)", suggestion: "Remove secondary or use proper modifier" }
    ]}
  ];

  const exports = [
    { id: 4, claim_id: 1, file_path: "/exports/edi/claim_1_20250823235745.txt", status: "SENT", sha256: "3b4232...ef72" },
    { id: 5, claim_id: 1, file_path: "/exports/edi/claim_1_20250824101501.txt", status: "QUEUED", sha256: "88aa90...ff10" },
  ];

  const bundle = {
    resourceType: "Bundle",
    type: "collection",
    entry: [
      { resource: { resourceType: "Patient", id: "1", name: [{ family: "Doe", given: ["John"] }], birthDate: "1980-01-01" } },
      { resource: { resourceType: "Coverage", id: "1", payor: [{ display: "Sample Health" }], subscriberId: "ABC12345", beneficiary: { reference: "Patient/1" } } },
    ],
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-10 bg-white border-b border-slate-200">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-semibold">EHR Starter – API‑First Dashboard (Preview)</h1>
          <div className="text-sm text-slate-500">Local demo • No PHI • Simulated data</div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {/* Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-3">
          {tabs.map(t => (
            <button key={t} onClick={() => setActive(t)}
              className={`px-3 py-1.5 rounded-full text-sm border ${active===t? 'bg-slate-900 text-white border-slate-900':'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'}`}>
              {t}
            </button>
          ))}
        </div>

        {active === "Overview" && (
          <section className="space-y-6">
            {/* KPI cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {stats.map(s => (
                <div key={s.label} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-200">
                  <div className="text-slate-500 text-sm">{s.label}</div>
                  <div className="text-2xl font-semibold mt-1">{s.value}</div>
                </div>
              ))}
            </div>

            {/* Patient + Coverage */}
            <div className="grid md:grid-cols-2 gap-4">
              <Card title="Patient">
                <KV label="Name" value={`${patient.first_name} ${patient.last_name}`} />
                <KV label="DOB" value={patient.date_of_birth} />
                <KV label="Phone" value={patient.phone} />
                <KV label="Email" value={patient.email} />
                <KV label="Address" value={`${patient.address.line}, ${patient.address.city}, ${patient.address.state} ${patient.address.postal}`} />
              </Card>
              <Card title="Coverage">
                <KV label="Payer" value={coverage.payer_name} />
                <KV label="Member ID" value={coverage.member_id} />
                <KV label="Group" value={coverage.group_number} />
                <KV label="Effective" value={coverage.effective_date} />
                <KV label="Plan" value={coverage.plan.product} />
              </Card>
            </div>

            {/* Claim summary */}
            <Card title={`Claim #${claim.id} • POS ${claim.pos}`}>
              <div className="text-sm text-slate-600 mb-2">Total Charge: ${claim.total_charge.toFixed(2)}</div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500">
                    <th className="py-1">CPT</th>
                    <th className="py-1">Units</th>
                    <th className="py-1">Charge</th>
                  </tr>
                </thead>
                <tbody>
                  {claim.lines.map(l => (
                    <tr key={l.id} className="border-t border-slate-200">
                      <td className="py-1">{l.cpt}</td>
                      <td className="py-1">{l.units}</td>
                      <td className="py-1">${l.charge.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          </section>
        )}

        {active === "Workqueue" && (
          <section>
            <Card title="Blocking Errors (Scrub)">
              {workqueue.length === 0 ? (
                <Empty text="No blocking errors – you’re clear to submit." />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-slate-500">
                        <th className="py-1">Claim</th>
                        <th className="py-1">Payer</th>
                        <th className="py-1">Charge</th>
                        <th className="py-1">Errors</th>
                      </tr>
                    </thead>
                    <tbody>
                      {workqueue.map(w => (
                        <tr key={w.id} className="border-t border-slate-200 align-top">
                          <td className="py-2">#{w.id}</td>
                          <td className="py-2">{w.payer_name}</td>
                          <td className="py-2">${w.total_charge.toFixed(2)}</td>
                          <td className="py-2 space-y-1">
                            {w.errors.map((e, i) => (
                              <div key={i} className="bg-red-50 border border-red-200 text-red-800 px-2 py-1 rounded">
                                <b>{e.code}</b>: {e.message}
                              </div>
                            ))}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </section>
        )}

        {active === "Claim #1" && (
          <section className="grid md:grid-cols-2 gap-4">
            <Card title="Lines">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500">
                    <th className="py-1">CPT</th>
                    <th className="py-1">Units</th>
                    <th className="py-1">Charge</th>
                  </tr>
                </thead>
                <tbody>
                  {claim.lines.map(l => (
                    <tr key={l.id} className="border-t border-slate-200">
                      <td className="py-1">{l.cpt}</td>
                      <td className="py-1">{l.units}</td>
                      <td className="py-1">${l.charge.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
            <Card title="Auto‑fix Preview">
              <ul className="list-disc pl-5 text-sm text-slate-700 space-y-1">
                <li>POS_CONFLICT → set POS to 11 (Office) when office E/M codes present</li>
                <li>MUE_EXCEEDED → cap units to table limit</li>
                <li>NCCI_PAIR → drop secondary conflicting code</li>
                <li>REQUIRED_PAYER_NAME → fill from latest Coverage</li>
                <li>TOTAL_CHARGE_ZERO → sum (units × charge)</li>
              </ul>
              <div className="mt-3 text-xs text-slate-500">Use API: <code>/api/claims/1/autofix/</code> (GET=preview, POST ?apply=1=apply)</div>
            </Card>
          </section>
        )}

        {active === "Eligibility" && (
          <section className="grid md:grid-cols-2 gap-4">
            <Card title="Eligibility Snapshot">
              <KV label="Status" value={eligibility.payload.active ? "Active" : "Inactive"} />
              <KV label="Network" value={eligibility.payload.network_status} />
              <div className="mt-3">
                <div className="text-sm font-medium mb-1">Benefits</div>
                <div className="space-y-2">
                  {eligibility.payload.benefits.map((b, i) => (
                    <div key={i} className="border border-slate-200 rounded-lg p-3 bg-white">
                      <div className="font-medium">{b.category}</div>
                      <div className="text-sm text-slate-600">{b.copay !== null ? `Copay $${b.copay}` : `Coins ${Math.round(b.coinsurance*100)}%`}</div>
                      <div className="text-xs text-slate-500">Deductible remaining: ${b.deductibleRemaining}</div>
                    </div>
                  ))}
                </div>
                <div className="text-xs text-slate-500 mt-2">Mode: {eligibility.payload.raw.mode}</div>
              </div>
            </Card>
            <Card title="Cost Estimate (stub)">
              <p className="text-sm text-slate-700">Uses copay if available; else applies deductible remaining and coinsurance to the claim total.</p>
              <div className="mt-3 text-sm">Example for Office Visit on $150: <b>$40</b> (copay)</div>
              <div className="text-xs text-slate-500 mt-1">API: <code>/api/claims/1/estimate/</code></div>
            </Card>
          </section>
        )}

        {active === "Exports" && (
          <section>
            <Card title="EDI 837 Exports">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500">
                      <th className="py-1">ID</th>
                      <th className="py-1">Claim</th>
                      <th className="py-1">Status</th>
                      <th className="py-1">File</th>
                    </tr>
                  </thead>
                  <tbody>
                    {exports.map(e => (
                      <tr key={e.id} className="border-t border-slate-200">
                        <td className="py-1">{e.id}</td>
                        <td className="py-1">#{e.claim_id}</td>
                        <td className="py-1"><span className={`px-2 py-0.5 rounded-full text-xs ${e.status==='SENT'?'bg-emerald-50 text-emerald-700 border border-emerald-200':'bg-amber-50 text-amber-700 border border-amber-200'}`}>{e.status}</span></td>
                        <td className="py-1 truncate max-w-xs" title={e.file_path}>{e.file_path}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="text-xs text-slate-500 mt-2">Download via API: <code>/api/claims/exports/&lt;id&gt;/download/</code></div>
            </Card>
          </section>
        )}

        {active === "FHIR Bundle" && (
          <section>
            <Card title="Patient + Coverages (FHIR Bundle)">
              <pre className="bg-slate-900 text-slate-100 p-4 rounded-xl text-xs overflow-auto">{JSON.stringify(bundle, null, 2)}</pre>
              <div className="text-xs text-slate-500 mt-2">API: <code>/api/fhir/Bundle/PatientCoverages/1</code></div>
            </Card>
          </section>
        )}
      </main>
    </div>
  );
}

function Card({ title, children }) {
  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-200">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function KV({ label, value }) {
  return (
    <div className="flex items-center justify-between text-sm py-1">
      <div className="text-slate-500">{label}</div>
      <div className="font-medium text-slate-900">{String(value)}</div>
    </div>
  );
}

function Empty({ text }) {
  return (
    <div className="p-6 text-center border border-dashed border-slate-300 rounded-xl text-slate-500 bg-slate-50">
      {text}
    </div>
  );
}
