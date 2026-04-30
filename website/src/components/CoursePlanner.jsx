import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  COURSES,
  TRACKS,
  analyzeGraduationPlan,
  parseTakenCourses,
} from '../data/coursePlanner';
import './CoursePlanner.css';

const defaultTaken = 'MA16100, MA16200, CS19300, CS18000, CS18200, CS24000';

const buildGraphLayout = (nodes, edges) => {
  const width = 1120;
  const columnWidth = 170;
  const rowHeight = 82;
  const grouped = nodes.reduce((acc, node) => {
    const depth = Math.min(node.depth, 6);
    acc[depth] = acc[depth] || [];
    acc[depth].push(node);
    return acc;
  }, {});
  const maxRows = Math.max(1, ...Object.values(grouped).map((group) => group.length));
  const height = Math.max(420, maxRows * rowHeight + 80);
  const positioned = {};

  Object.entries(grouped).forEach(([depth, group]) => {
    const x = 48 + Number(depth) * columnWidth;
    const offset = Math.max(0, (maxRows - group.length) * rowHeight * 0.5);
    group.forEach((node, index) => {
      positioned[node.code] = {
        ...node,
        x,
        y: 44 + offset + index * rowHeight,
      };
    });
  });

  const visibleEdges = edges
    .filter((edge) => positioned[edge.from] && positioned[edge.to])
    .map((edge) => ({
      ...edge,
      x1: positioned[edge.from].x + 118,
      y1: positioned[edge.from].y + 22,
      x2: positioned[edge.to].x,
      y2: positioned[edge.to].y + 22,
    }));

  return { width, height, nodes: Object.values(positioned), edges: visibleEdges };
};

const CoursePlanner = () => {
  const navigate = useNavigate();
  const [track, setTrack] = useState('machine_intelligence');
  const [takenInput, setTakenInput] = useState(defaultTaken);
  const [creditsPerSemester, setCreditsPerSemester] = useState(15);

  const analysis = useMemo(() => analyzeGraduationPlan({
    track,
    takenCourses: parseTakenCourses(takenInput),
    creditsPerSemester,
  }), [track, takenInput, creditsPerSemester]);

  const graph = useMemo(
    () => buildGraphLayout(analysis.nodes, analysis.edges),
    [analysis.nodes, analysis.edges]
  );

  return (
    <div className="planner-page">
      <header className="app-shell-nav">
        <div className="brand-mark" aria-label="AI Student Advisor">
          <span>AI</span>
          <strong>Student Advisor</strong>
        </div>
        <nav>
          <button type="button" onClick={() => navigate('/chat')}>CHAT</button>
          <button type="button" className="active">COURSE GRAPH</button>
          <button type="button" onClick={() => navigate('/vote')}>VOTING</button>
        </nav>
      </header>

      <main className="planner-shell">
        <section className="planner-hero">
          <div>
            <p className="eyebrow">PURDUE CS TRACK PLANNER</p>
            <h1>Graduation path graph</h1>
            <p>
              Paste completed courses, choose a track, and see the smallest remaining
              core/track set with prerequisite flow.
            </p>
          </div>
          <div className="hero-stats">
            <div>
              <span>{analysis.minimumClassesRemaining}</span>
              <small>classes left</small>
            </div>
            <div>
              <span>{analysis.minimumCreditsRemaining}</span>
              <small>credits left</small>
            </div>
            <div>
              <span>{analysis.plan.length}</span>
              <small>planned terms</small>
            </div>
          </div>
        </section>

        <section className="planner-controls">
          <label>
            Track
            <select value={track} onChange={(event) => setTrack(event.target.value)}>
              {Object.entries(TRACKS).map(([key, data]) => (
                <option key={key} value={key}>{data.display}</option>
              ))}
            </select>
          </label>
          <label>
            Credits per semester
            <input
              type="number"
              min="1"
              max="18"
              value={creditsPerSemester}
              onChange={(event) => setCreditsPerSemester(event.target.value)}
            />
          </label>
          <label className="taken-input">
            Completed courses
            <textarea
              value={takenInput}
              onChange={(event) => setTakenInput(event.target.value)}
              placeholder="CS18000, CS18200, MA16100..."
            />
          </label>
        </section>

        <section className="planner-summary-grid">
          <article>
            <h2>Core</h2>
            <strong>{analysis.completedCore.length}/7 complete</strong>
            <p>{analysis.coreRemaining.length ? analysis.coreRemaining.join(', ') : 'All core courses are complete.'}</p>
          </article>
          <article>
            <h2>Track</h2>
            <strong>{analysis.trackName}</strong>
            <p>{analysis.trackSlotsCompleted}/{analysis.trackSlotsTotal} requirement slots currently satisfied.</p>
          </article>
          <article>
            <h2>Available Next</h2>
            <strong>{analysis.availableNext.length || 0} courses</strong>
            <p>{analysis.availableNext.length ? analysis.availableNext.slice(0, 7).join(', ') : 'No generated next courses.'}</p>
          </article>
        </section>

        <section className="graph-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">VISUALIZATION</p>
              <h2>Prerequisite graph</h2>
            </div>
            <div className="graph-legend">
              <span className="taken">Taken</span>
              <span className="core">Core</span>
              <span className="track">Track</span>
              <span className="prereq">Prereq</span>
            </div>
          </div>

          <div className="graph-scroll">
            <svg viewBox={`0 0 ${graph.width} ${graph.height}`} role="img" aria-label="Course prerequisite graph">
              <defs>
                <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
                  <path d="M0,0 L0,6 L9,3 z" />
                </marker>
              </defs>
              {graph.edges.map((edge) => (
                <path
                  key={`${edge.from}-${edge.to}`}
                  className="graph-edge"
                  d={`M ${edge.x1} ${edge.y1} C ${edge.x1 + 46} ${edge.y1}, ${edge.x2 - 46} ${edge.y2}, ${edge.x2} ${edge.y2}`}
                  markerEnd="url(#arrow)"
                />
              ))}
              {graph.nodes.map((node) => (
                <g className={`graph-node ${node.status}`} key={node.code} transform={`translate(${node.x}, ${node.y})`}>
                  <rect width="132" height="50" rx="22" />
                  <text x="66" y="21" textAnchor="middle">{node.code}</text>
                  <text x="66" y="37" textAnchor="middle">{node.credits} cr</text>
                </g>
              ))}
            </svg>
          </div>
        </section>

        <section className="plan-grid">
          <div className="section-heading">
            <div>
              <p className="eyebrow">MINIMUM GENERATED SET</p>
              <h2>Semester plan</h2>
            </div>
          </div>
          {analysis.plan.map((semester) => (
            <article className="semester-card" key={semester.semester}>
              <div>
                <span>Semester {semester.semester}</span>
                <strong>{semester.credits} credits</strong>
              </div>
              <ul>
                {semester.courses.map((code) => (
                  <li key={code}>
                    <span>{code}</span>
                    <small>{COURSES[code]?.title}</small>
                  </li>
                ))}
              </ul>
            </article>
          ))}
          {analysis.unscheduled.length ? (
            <article className="semester-card warning">
              <div>
                <span>Needs review</span>
                <strong>{analysis.unscheduled.length} unscheduled</strong>
              </div>
              <p>{analysis.unscheduled.join(', ')}</p>
            </article>
          ) : null}
        </section>
      </main>
    </div>
  );
};

export default CoursePlanner;
