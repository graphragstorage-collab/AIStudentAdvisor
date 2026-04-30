const COURSE = (code) => ({ type: 'course', code });
const ALL = (...args) => ({ type: 'all', args });
const ANY = (...args) => ({ type: 'any', args });

export const COURSES = {};

const addCourse = (code, title, credits, prereq = null, autoSelect = true) => {
  COURSES[code] = { code, title, credits, prereq, autoSelect };
};

addCourse('MA16100', 'Plane Analytic Geometry and Calculus I', 5);
addCourse('MA16200', 'Plane Analytic Geometry and Calculus II', 5, COURSE('MA16100'));
addCourse('MA26100', 'Multivariate Calculus', 4, COURSE('MA16200'));
addCourse('MA26500', 'Linear Algebra', 3, COURSE('MA26100'));
addCourse('STAT35000', 'Introduction to Statistics', 3, COURSE('MA16200'));
addCourse('MA26600', 'Ordinary Differential Equations', 3, COURSE('MA26100'));
addCourse('MA36600', 'Ordinary Differential Equations', 4, COURSE('MA26500'));
addCourse('STAT41600', 'Probability', 3, COURSE('MA26100'));
addCourse('STAT51200', 'Applied Regression Analysis', 3, ANY(COURSE('STAT35000'), COURSE('STAT35500'), COURSE('STAT41700'), COURSE('STAT51100')));
addCourse('MA38500', 'Introduction to Logic', 3, COURSE('MA26100'));
addCourse('MA45300', 'Elements of Algebra I', 3, ANY(COURSE('MA26500'), COURSE('MA35100'), COURSE('MA35200')));
addCourse('MA34100', 'Foundations of Analysis', 3, COURSE('MA26100'));

addCourse('CS19300', 'Tools', 1);
addCourse('CS18000', 'Problem Solving and Object-Oriented Programming', 4, COURSE('MA16100'));
addCourse('CS18200', 'Foundations of Computer Science', 3, ALL(COURSE('CS18000'), COURSE('MA16100')));
addCourse('CS24000', 'Programming in C', 3, COURSE('CS18000'));
addCourse('CS25000', 'Computer Architecture', 4, ALL(COURSE('CS18200'), COURSE('CS24000')));
addCourse('CS25100', 'Data Structures and Algorithms', 3, ALL(COURSE('CS18200'), COURSE('CS24000')));
addCourse('CS25200', 'Systems Programming', 4, ALL(COURSE('CS25000'), COURSE('CS25100')));
addCourse('CS30700', 'Software Engineering I', 3, ANY(COURSE('CS25100'), COURSE('CS25300')));
addCourse('CS31100', 'Competitive Programming II', 2, ANY(COURSE('CS21100'), COURSE('CS38100')));
addCourse('CS31400', 'Numerical Methods', 3, ALL(COURSE('CS18000'), ANY(COURSE('MA26200'), COURSE('MA26500'), COURSE('MA35000'), COURSE('MA35100'))));
addCourse('CS33400', 'Fundamentals of Computer Graphics', 3, ALL(ANY(COURSE('MA26500'), COURSE('MA35000'), COURSE('MA35100')), ANY(COURSE('CS24000'), COURSE('ECE36800'))));
addCourse('CS34800', 'Information Systems', 3, ANY(COURSE('CS25100'), COURSE('CS25300'), COURSE('ECE36800')));
addCourse('CS35100', 'Cloud Computing', 3, COURSE('CS25200'));
addCourse('CS35200', 'Compilers: Principles and Practice', 3, ALL(COURSE('CS25100'), COURSE('CS25200')));
addCourse('CS35300', 'Principles of Concurrency and Parallelism', 3, ALL(COURSE('CS25100'), COURSE('CS25200'), COURSE('CS35200')));
addCourse('CS35400', 'Operating Systems', 3, ALL(COURSE('CS25100'), COURSE('CS25200')));
addCourse('CS35500', 'Introduction to Cryptography', 3, ALL(ANY(COURSE('CS25100'), COURSE('CS25300'), COURSE('ECE36800')), ANY(COURSE('MA26200'), COURSE('MA26500'), COURSE('MA35000'), COURSE('MA35100'), COURSE('STAT35000'), COURSE('STAT51100'))));
addCourse('CS37300', 'Data Mining and Machine Learning', 3, ALL(COURSE('CS18200'), ANY(COURSE('CS25100'), COURSE('CS25300')), ANY(COURSE('STAT35000'), COURSE('STAT35500'), COURSE('STAT51100'))));
addCourse('CS38100', 'Introduction to the Analysis of Algorithms', 3, ALL(ANY(COURSE('CS25100'), COURSE('CS25300'), COURSE('ECE36800'), COURSE('ECE36900')), COURSE('MA26100')));
addCourse('CS39000AALG', 'Advanced Topics in Algorithms', 3, null, false);
addCourse('CS40700', 'Software Engineering Senior Project', 3, COURSE('CS30700'));
addCourse('CS40800', 'Software Testing', 3, ANY(COURSE('CS25100'), COURSE('CS25300')));
addCourse('CS41100', 'Competitive Programming III', 2, COURSE('CS31100'));
addCourse('CS42200', 'Computer Networks', 3, ALL(COURSE('CS35400'), COURSE('CS25100'), COURSE('CS25200')));
addCourse('CS42600', 'Computer Security', 3, ALL(COURSE('CS25100'), COURSE('CS25200')));
addCourse('CS43400', 'Advanced Computer Graphics', 3, COURSE('CS33400'));
addCourse('CS43900', 'Introduction to Data Visualization', 3, ANY(COURSE('CS25100'), COURSE('CS25300')));
addCourse('CS44000', 'Large Scale Data Analytics', 3, ALL(COURSE('CS37300'), COURSE('STAT41700')), false);
addCourse('CS44800', 'Introduction to Relational Database Systems', 3, ANY(COURSE('CS25100'), COURSE('CS25300')));
addCourse('CS45600', 'Programming Languages', 3, COURSE('CS35200'));
addCourse('CS45800', 'Introduction to Robotics', 3, ANY(COURSE('CS25100'), COURSE('CS25300')));
addCourse('CS47100', 'Introduction to Artificial Intelligence', 3, ANY(COURSE('CS25100'), COURSE('CS25300'), COURSE('ECE36800')));
addCourse('CS47300', 'Web Information Search and Management', 3, ANY(COURSE('CS25100'), COURSE('CS25300'), COURSE('ECE36800')));
addCourse('CS47500', 'Human-Computer Interaction', 3, ANY(COURSE('CS25100'), COURSE('CS25300')));
addCourse('CS47800', 'Introduction to Bioinformatics', 3, ALL(ANY(COURSE('BIOL23000'), COURSE('BIOL23100')), COURSE('BIOL24100'), COURSE('CS18000')));
addCourse('CS48300', 'Introduction to the Theory of Computation', 3, ANY(COURSE('CS38100'), COURSE('CS39000AALG')));
addCourse('CS48900', 'Embedded Systems', 3, ALL(COURSE('CS25000'), COURSE('CS25100'), COURSE('CS25200')));

[
  ['CS49000DSO', 'Distributed Systems'], ['CS49000SWS', 'Software Security'], ['CS49000VR', 'Introduction to VR/AR'],
  ['CS49000SENIORPROJECT', 'Senior Project'], ['CS49700', 'Honors Research Project'], ['CS51000', 'Software Engineering'],
  ['CS51400', 'Numerical Analysis'], ['CS51500', 'Numerical Linear Algebra'], ['CS52000', 'Computational Methods in Optimization'],
  ['CS52500', 'Parallel Computing'], ['CS56000', 'Reasoning About Programs'], ['CS57700', 'Natural Language Processing'],
  ['CS57800', 'Statistical Machine Learning'], ['CS59000SRS', 'Software Reliability and Security'], ['EPCS41100', 'EPICS Senior Design I'],
  ['EPCS41200', 'EPICS Senior Design II'], ['ECE30100', 'Signals and Systems'], ['IE33500', 'Operations Research - Optimization'],
  ['IE33600', 'Operations Research - Stochastic Models'], ['MA35301', 'Linear Algebra II'], ['MA36200', 'Topics in Vector Calculus'],
  ['MA42100', 'Linear Programming and Optimization Techniques'], ['MA44000', 'Analysis II'], ['CS21100', 'Competitive Programming I'],
  ['CS25300', 'Data Structures and Algorithms for DS/AI'], ['ECE36800', 'Data Structures'], ['ECE36900', 'Discrete Mathematics for Engineers'],
  ['ECE46900', 'Operating Systems Engineering'], ['STAT35500', 'Statistics for Data Science'], ['STAT51100', 'Statistical Methods'],
  ['STAT41700', 'Statistical Theory'], ['MA26200', 'Linear Algebra and Differential Equations'], ['MA35000', 'Linear Algebra I'],
  ['MA35100', 'Elementary Linear Algebra'], ['MA35200', 'Linear Algebra II'], ['MA35300', 'Linear Algebra I'],
  ['MA51100', 'Linear Algebra'], ['BIOL23000', 'Structure and Function of Organisms I'], ['BIOL23100', 'Structure and Function of Organisms II'],
  ['BIOL24100', 'Genetics'],
].forEach(([code, title]) => addCourse(code, title, 3, null, false));

export const CORE_REQUIRED = ['CS19300', 'CS18000', 'CS18200', 'CS24000', 'CS25000', 'CS25100', 'CS25200'];

const option = (courses, tags = [], autoSelect = null, csCount = null) => {
  const courseList = Array.isArray(courses) ? courses : [courses];
  const inferredAuto = courseList.every((code) => COURSES[code]?.autoSelect);
  return {
    courses: courseList,
    tags,
    autoSelect: autoSelect ?? inferredAuto,
    csCount: csCount ?? (courseList.every((code) => code.startsWith('CS')) ? 1 : 0),
  };
};

const repeatSlots = (count, options) => Array.from({ length: count }, () => options);
const ALGO_SLOT = [option('CS38100'), option('CS39000AALG', [], false)];

export const TRACKS = {
  computational_science_and_engineering: {
    display: 'Computational Science and Engineering',
    minCsSlots: 4,
    slots: [
      [option('MA26600', [], true, 0), option('MA36600', [], true, 0)],
      [option('CS31400')],
      ALGO_SLOT,
      [option('CS37300'), option('CS47300'), option('CS47800'), option('IE33600', [], false, 0), option('ECE30100', [], false, 0)],
      [option('CS35200'), option('CS35300'), option('CS35400')],
      ...repeatSlots(2, [option('CS30700'), option('CS42200'), option('CS45600'), option('CS45800'), option('CS47100'), option('CS48300'), option('CS51400', [], false), option('CS51500', [], false), option('CS52000', [], false), option('CS52500', [], false), option('IE33500', [], false, 0), option('MA34100', [], true, 0), option('MA44000', [], false, 0), option('CS37300'), option('CS47300'), option('CS47800'), option('CS35200'), option('CS35300'), option('CS35400')]),
    ],
  },
  computer_graphics_and_visualization: {
    display: 'Computer Graphics and Visualization',
    slots: [[option('CS31400')], [option('CS33400')], [option('CS37300'), option('CS43400'), option('CS47100')], ...repeatSlots(3, [option('CS35200'), option('CS35400'), option('CS37300'), option('CS38100'), option('CS39000AALG', [], false), option('CS42200'), option('CS43400'), option('CS43900'), option('CS45600'), option('CS45800'), option('CS47100'), option('CS49000VR', [], false)])],
  },
  database_and_information_systems: {
    display: 'Database and Information Systems',
    slots: [[option('CS34800')], ALGO_SLOT, [option('CS44800')], [option('CS37300'), option('CS47300')], [option('CS35200'), option('CS35300'), option('CS35400')], [option('CS35500'), option('CS42600')], [option('CS37300'), option('CS42200'), option('CS47100'), option('CS47300'), option('CS47800'), option('CS48300'), option('CS49000SENIORPROJECT', [], false), option('CS49700', [], false), option(['EPCS41100', 'EPCS41200'], [], false, 0)]],
  },
  algorithmic_foundations: {
    display: 'Algorithmic Foundations',
    slots: [[option('CS35200'), option('CS35400')], [option('CS37300'), option('CS47100')], ALGO_SLOT, ...repeatSlots(3, [option(['CS31100', 'CS41100']), option('CS31400'), option('CS33400'), option('CS35300'), option('CS35500'), option('CS44800'), option('CS45600'), option('CS45800'), option('CS48300'), option('MA34100', [], true, 0), option('MA35300', [], false, 0), option('MA35301', [], false, 0), option('MA36200', [], false, 0), option('MA36600', [], true, 0), option('MA38500', [], true, 0), option('MA42100', [], false, 0), option('MA45300', [], true, 0)])],
  },
  machine_intelligence: {
    display: 'Machine Intelligence',
    slots: [[option('CS37300')], ALGO_SLOT, [option('CS47100'), option('CS47300')], [option('STAT41600', [], true, 0), option('STAT51200', [], true, 0)], ...repeatSlots(2, [option('CS31400'), option('CS34800'), option('CS35200'), option('CS44800'), option('CS45600'), option('CS45800'), option('CS47100'), option('CS47300'), option('CS48300'), option('CS43900'), option('CS44000', [], false), option('CS47500'), option('CS57700', [], false), option('CS57800', [], false), option(['CS31100', 'CS41100'], [], false)])],
  },
  programming_languages: {
    display: 'Programming Languages',
    slots: [[option('CS35200')], [option('CS35400')], [option('CS45600')], ...repeatSlots(3, [option('CS30700', ['pl_line1']), option('CS40800', ['pl_line1']), option('CS34800', ['pl_line2']), option('CS44800', ['pl_line2']), option('CS35300'), option('CS38100'), option('CS39000AALG', [], false), option('CS42600'), option('CS48300'), option('CS56000', [], false), option('MA38500', ['pl_line3'], true, 0), option('MA45300', ['pl_line3'], true, 0)])],
  },
  security: {
    display: 'Security',
    slots: [[option('CS35400')], [option('CS35500')], [option('CS42600')], ...repeatSlots(3, [option('CS30700', ['sec_line1']), option('CS40800', ['sec_line1']), option('CS34800', ['sec_line2']), option('CS44800', ['sec_line2']), option('CS47300', ['sec_line2']), option('CS35200'), option('CS35300', ['sec_line4']), option('CS45600', ['sec_line4']), option('CS37300', ['sec_line5']), option('CS47100', ['sec_line5']), option('CS38100'), option('CS39000AALG', [], false), option('CS42200'), option('CS48900', ['sec_line8']), option('CS49000DSO', ['sec_line8'], false), option('CS49000SWS', [], false)])],
  },
  software_engineering: {
    display: 'Software Engineering',
    slots: [[option('CS30700')], [option('CS35200'), option('CS35400')], ALGO_SLOT, [option('CS40800')], [option('CS40700')], [option(['CS31100', 'CS41100']), option('CS34800'), option('CS35100'), option('CS35200'), option('CS35300'), option('CS35400'), option('CS37300'), option('CS42200'), option('CS42600'), option('CS44800'), option('CS45600'), option('CS47100'), option('CS47300'), option('CS48900'), option('CS49000DSO', [], false), option('CS49000SWS', [], false), option('CS51000', [], false), option('CS59000SRS', [], false)]],
  },
  systems_software: {
    display: 'Systems Software',
    slots: [[option('CS35200')], [option('CS35400')], [option('CS42200')], ...repeatSlots(3, [option('CS30700'), option(['CS31100', 'CS41100']), option('CS33400'), option('CS35100'), option('CS35300'), option('CS38100'), option('CS39000AALG', [], false), option('CS42600'), option('CS44800'), option('CS45600'), option('CS48900'), option('CS49000DSO', [], false), option('CS49000VR', [], false), option('CS49000SENIORPROJECT', [], false)])],
  },
};

const TRACK_ALIASES = {
  machineintelligence: 'machine_intelligence',
  mi: 'machine_intelligence',
  computationalscienceandengineering: 'computational_science_and_engineering',
  cse: 'computational_science_and_engineering',
  computergraphicsandvisualization: 'computer_graphics_and_visualization',
  graphics: 'computer_graphics_and_visualization',
  cgv: 'computer_graphics_and_visualization',
  databaseandinformationsystems: 'database_and_information_systems',
  database: 'database_and_information_systems',
  dbis: 'database_and_information_systems',
  algorithmicfoundations: 'algorithmic_foundations',
  foundations: 'algorithmic_foundations',
  af: 'algorithmic_foundations',
  programminglanguages: 'programming_languages',
  pl: 'programming_languages',
  security: 'security',
  softwareengineering: 'software_engineering',
  softeng: 'software_engineering',
  systemssoftware: 'systems_software',
  systemsoftware: 'systems_software',
  systemsprogramming: 'systems_software',
};

const CODE_ALIASES = {
  MA41600: 'STAT41600',
  EE36800: 'ECE36800',
  EE46900: 'ECE46900',
  BIOL47800: 'CS47800',
  MATH26100: 'MA26100',
  MATH26200: 'MA26200',
  MA16300: 'MA16100',
  MA16500: 'MA16100',
  MATH16500: 'MA16100',
  MA16700: 'MA16100',
  MA17400: 'MA26100',
  MA18200: 'MA26100',
  MA26300: 'MA26100',
  MA27100: 'MA26100',
  MA27101: 'MA26100',
};

const TITLE_ALIASES = Object.fromEntries(
  Object.values(COURSES).map((course) => [course.title.toUpperCase().replace(/[^A-Z0-9]+/g, ''), course.code])
);

export const normalizeTrack = (track) => {
  const key = String(track || '').toLowerCase().replace(/[^a-z0-9]+/g, '');
  return TRACK_ALIASES[key] || (TRACKS[track] ? track : 'machine_intelligence');
};

export const normalizeCourse = (raw) => {
  const compact = String(raw || '').toUpperCase().replace(/[^A-Z0-9]+/g, '');
  if (!compact) return '';
  if (TITLE_ALIASES[compact]) return TITLE_ALIASES[compact];
  const match = compact.match(/^([A-Z]+)(\d{3,5})([A-Z0-9]*)$/);
  if (!match) return CODE_ALIASES[compact] || compact;
  const [, subject, digits, suffix] = match;
  const code = `${subject}${digits.padEnd(5, '0')}${suffix}`;
  return CODE_ALIASES[code] || code;
};

export const parseTakenCourses = (input) => (
  String(input || '')
    .split(/[\n,;]+/)
    .map(normalizeCourse)
    .filter(Boolean)
);

const evalExpr = (expr, takenSet) => {
  if (!expr) return true;
  if (expr.type === 'course') return takenSet.has(expr.code);
  if (expr.type === 'all') return expr.args.every((arg) => evalExpr(arg, takenSet));
  if (expr.type === 'any') return expr.args.some((arg) => evalExpr(arg, takenSet));
  return false;
};

const referencedCourses = (expr) => {
  if (!expr) return [];
  if (expr.type === 'course') return [expr.code];
  return expr.args.flatMap(referencedCourses);
};

const diffCourses = (courses, takenSet, usedSet) => courses.filter((code) => !takenSet.has(code) && !usedSet.has(code));

const optionRank = (opt, takenSet, usedSet) => {
  const missing = diffCourses(opt.courses, takenSet, usedSet);
  const credits = missing.reduce((sum, code) => sum + (COURSES[code]?.credits || 3), 0);
  return [missing.length, credits, opt.autoSelect ? 0 : 1, opt.courses.join('-')];
};

const betterRank = (left, right) => {
  for (let i = 0; i < left.length; i += 1) {
    if (left[i] < right[i]) return true;
    if (left[i] > right[i]) return false;
  }
  return false;
};

const chooseTrackCourses = (trackKey, takenSet) => {
  const track = TRACKS[trackKey];
  const memo = new Map();

  const dfs = (slotIndex, usedCourses, usedTags, csSlots) => {
    const memoKey = `${slotIndex}|${[...usedCourses].sort().join(',')}|${[...usedTags].sort().join(',')}|${csSlots}`;
    if (memo.has(memoKey)) return memo.get(memoKey);
    if (slotIndex === track.slots.length) {
      const valid = csSlots >= (track.minCsSlots || 0);
      return valid ? { courses: [], rank: [0, 0, 0, ''] } : null;
    }

    let best = null;
    track.slots[slotIndex].forEach((opt) => {
      if (opt.courses.some((code) => usedCourses.has(code))) return;
      if (opt.tags.some((tag) => usedTags.has(tag))) return;

      const nextUsed = new Set([...usedCourses, ...opt.courses]);
      const nextTags = new Set([...usedTags, ...opt.tags]);
      const suffix = dfs(slotIndex + 1, nextUsed, nextTags, csSlots + opt.csCount);
      if (!suffix) return;

      const missing = diffCourses(opt.courses, takenSet, usedCourses);
      const localRank = optionRank(opt, takenSet, usedCourses);
      const candidate = {
        courses: [...missing, ...suffix.courses],
        rank: [
          localRank[0] + suffix.rank[0],
          localRank[1] + suffix.rank[1],
          localRank[2] + suffix.rank[2],
          `${localRank[3]}|${suffix.rank[3]}`,
        ],
      };

      if (!best || betterRank(candidate.rank, best.rank)) best = candidate;
    });

    memo.set(memoKey, best);
    return best;
  };

  return dfs(0, new Set(), new Set(), 0) || { courses: [], rank: [0, 0, 0, ''] };
};

const bestPrereqCourses = (expr, availableSet) => {
  if (!expr) return [];
  if (expr.type === 'course') return availableSet.has(expr.code) ? [] : [expr.code];
  if (expr.type === 'all') {
    return [...new Set(expr.args.flatMap((arg) => bestPrereqCourses(arg, availableSet)))];
  }
  const branches = expr.args.map((arg) => bestPrereqCourses(arg, availableSet));
  branches.sort((a, b) => a.length - b.length || a.join('').localeCompare(b.join('')));
  return branches[0] || [];
};

const expandWithPrereqs = (seedCourses, takenSet) => {
  const needed = new Set(seedCourses.filter((code) => !takenSet.has(code)));
  let changed = true;
  while (changed) {
    changed = false;
    [...needed].forEach((code) => {
      const course = COURSES[code];
      if (!course) return;
      const available = new Set([...takenSet, ...needed]);
      bestPrereqCourses(course.prereq, available).forEach((prereq) => {
        if (!takenSet.has(prereq) && !needed.has(prereq)) {
          needed.add(prereq);
          changed = true;
        }
      });
    });
  }
  return needed;
};

const trackProgressCount = (trackKey, takenSet) => {
  const track = TRACKS[trackKey];
  const memo = new Map();
  const dfs = (slotIndex, usedCourses, usedTags) => {
    const memoKey = `${slotIndex}|${[...usedCourses].sort().join(',')}|${[...usedTags].sort().join(',')}`;
    if (memo.has(memoKey)) return memo.get(memoKey);
    if (slotIndex === track.slots.length) return 0;
    let best = dfs(slotIndex + 1, usedCourses, usedTags);
    track.slots[slotIndex].forEach((opt) => {
      if (!opt.courses.every((code) => takenSet.has(code))) return;
      if (opt.courses.some((code) => usedCourses.has(code))) return;
      if (opt.tags.some((tag) => usedTags.has(tag))) return;
      best = Math.max(best, 1 + dfs(
        slotIndex + 1,
        new Set([...usedCourses, ...opt.courses]),
        new Set([...usedTags, ...opt.tags])
      ));
    });
    memo.set(memoKey, best);
    return best;
  };
  return dfs(0, new Set(), new Set());
};

const planSemesters = (remainingSet, takenSet, creditCap) => {
  const remaining = new Set(remainingSet);
  const completed = new Set(takenSet);
  const plan = [];
  let guard = 0;

  while (remaining.size && guard < 16) {
    guard += 1;
    const available = [...remaining]
      .filter((code) => evalExpr(COURSES[code]?.prereq, completed))
      .sort((a, b) => {
        const coreDelta = CORE_REQUIRED.includes(b) - CORE_REQUIRED.includes(a);
        if (coreDelta) return coreDelta;
        return (COURSES[b]?.credits || 0) - (COURSES[a]?.credits || 0);
      });

    if (!available.length) break;

    const semester = [];
    let credits = 0;
    available.forEach((code) => {
      const courseCredits = COURSES[code]?.credits || 3;
      if (semester.length < 5 && credits + courseCredits <= creditCap) {
        semester.push(code);
        credits += courseCredits;
      }
    });

    semester.forEach((code) => {
      remaining.delete(code);
      completed.add(code);
    });
    plan.push({ semester: plan.length + 1, credits, courses: semester });
  }

  return { plan, unscheduled: [...remaining] };
};

const graphDepth = (code, nodes, memo = new Map()) => {
  if (memo.has(code)) return memo.get(code);
  const prereqs = referencedCourses(COURSES[code]?.prereq).filter((item) => nodes.has(item));
  if (!prereqs.length) {
    memo.set(code, 0);
    return 0;
  }
  const depth = 1 + Math.max(...prereqs.map((item) => graphDepth(item, nodes, memo)));
  memo.set(code, depth);
  return depth;
};

export const analyzeGraduationPlan = ({ track, takenCourses, creditsPerSemester = 15 }) => {
  const trackKey = normalizeTrack(track);
  const takenSet = new Set((takenCourses || []).map(normalizeCourse).filter(Boolean));
  const coreRemaining = CORE_REQUIRED.filter((code) => !takenSet.has(code));
  const chosenTrack = chooseTrackCourses(trackKey, takenSet);
  const directNeeded = new Set([...coreRemaining, ...chosenTrack.courses]);
  const remainingSet = expandWithPrereqs([...directNeeded], takenSet);
  const creditCap = Math.max(1, Math.min(Number(creditsPerSemester) || 15, 18));
  const semesterPlan = planSemesters(remainingSet, takenSet, creditCap);
  const nodeCodes = new Set([...takenSet, ...remainingSet]);
  const nodes = [...nodeCodes]
    .filter((code) => COURSES[code])
    .map((code) => {
      const status = takenSet.has(code) ? 'taken' : (coreRemaining.includes(code) ? 'core' : (chosenTrack.courses.includes(code) ? 'track' : 'prereq'));
      return {
        ...COURSES[code],
        status,
        depth: graphDepth(code, nodeCodes),
      };
    })
    .sort((a, b) => a.depth - b.depth || a.code.localeCompare(b.code));

  const edges = nodes.flatMap((node) => (
    referencedCourses(node.prereq)
      .filter((from) => nodeCodes.has(from) && COURSES[from])
      .map((from) => ({ from, to: node.code }))
  ));

  const completedCore = CORE_REQUIRED.filter((code) => takenSet.has(code));
  const trackDone = trackProgressCount(trackKey, takenSet);
  const availableNext = [...remainingSet]
    .filter((code) => evalExpr(COURSES[code]?.prereq, takenSet))
    .sort();

  return {
    trackKey,
    trackName: TRACKS[trackKey].display,
    taken: [...takenSet].sort(),
    completedCore,
    coreRemaining,
    trackSlotsCompleted: trackDone,
    trackSlotsTotal: TRACKS[trackKey].slots.length,
    remainingCourses: [...remainingSet].sort(),
    minimumClassesRemaining: remainingSet.size,
    minimumCreditsRemaining: [...remainingSet].reduce((sum, code) => sum + (COURSES[code]?.credits || 0), 0),
    plan: semesterPlan.plan,
    unscheduled: semesterPlan.unscheduled,
    availableNext,
    nodes,
    edges,
  };
};
