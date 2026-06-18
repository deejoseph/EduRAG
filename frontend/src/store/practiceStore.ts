import { create } from 'zustand';
import type { PracticePhase } from '../types/practice';

interface PracticeState {
  // 会话
  sessionId: string | null;
  topic: string;
  topicType: string;
  gradeLevel: string;
  status: 'idle' | 'in_progress' | 'completed';

  // 阶段
  currentPhase: number; // 0-3
  phases: PracticePhase[];

  // 计时器（正计时）
  phaseElapsed: number;    // 当前阶段已用秒数
  timerRunning: boolean;
  totalElapsed: number;    // 总已用秒数

  // 评估
  totalScore: number | null;

  // 成长日志
  includeInLog: boolean;

  // 保存记录
  saveToRecord: boolean;

  // Actions
  initSession: (sessionId: string, topic: string, topicType: string, gradeLevel: string, phases: PracticePhase[]) => void;
  setPhase: (phase: number) => void;
  setStudentContent: (phaseIndex: number, content: string) => void;
  submitPhase: (phaseIndex: number, feedback: string, references: any[]) => void;
  startPhaseTimer: () => void;
  tickPhaseTimer: () => void;
  pauseTimer: () => void;
  setTotalScore: (score: number | null) => void;
  setStatus: (status: 'idle' | 'in_progress' | 'completed') => void;
  incrementTotalElapsed: () => void;
  setIncludeInLog: (include: boolean) => void;
  setSaveToRecord: (save: boolean) => void;
  reset: () => void;
}

const initialState = {
  sessionId: null as string | null,
  topic: '',
  topicType: '材料作文',
  gradeLevel: '高中',
  status: 'idle' as const,
  currentPhase: 0,
  phases: [] as PracticePhase[],
  phaseElapsed: 0,
  timerRunning: false,
  totalElapsed: 0,
  totalScore: null as number | null,
  includeInLog: true,
  saveToRecord: true,
};

// interval ID 存模块级变量
let phaseTimerInterval: ReturnType<typeof setInterval> | null = null;
let elapsedInterval: ReturnType<typeof setInterval> | null = null;

export const usePracticeStore = create<PracticeState>((set, get) => ({
  ...initialState,

  initSession: (sessionId, topic, topicType, gradeLevel, phases) => {
    set({
      sessionId,
      topic,
      topicType,
      gradeLevel,
      phases,
      status: 'in_progress',
      currentPhase: 0,
      totalElapsed: 0,
      totalScore: null,
      includeInLog: true,
    });
    // 启动总计时
    if (elapsedInterval) clearInterval(elapsedInterval);
    elapsedInterval = setInterval(() => {
      get().incrementTotalElapsed();
    }, 1000);
  },

  setPhase: (phase) => {
    // 切换阶段时重置阶段计时
    if (phaseTimerInterval) clearInterval(phaseTimerInterval);
    set({ currentPhase: phase, phaseElapsed: 0, timerRunning: false });
  },

  setStudentContent: (phaseIndex, content) => set((state) => {
    const phases = [...state.phases];
    if (phases[phaseIndex]) {
      phases[phaseIndex] = { ...phases[phaseIndex], student_content: content };
    }
    return { phases };
  }),

  submitPhase: (phaseIndex, feedback, references) => set((state) => {
    const phases = [...state.phases];
    if (phases[phaseIndex]) {
      phases[phaseIndex] = {
        ...phases[phaseIndex],
        ai_feedback: feedback,
        ai_references: references,
        submitted_at: new Date().toISOString(),
      };
    }
    // 提交后停止阶段计时
    if (phaseTimerInterval) clearInterval(phaseTimerInterval);
    return { phases, timerRunning: false };
  }),

  startPhaseTimer: () => {
    if (phaseTimerInterval) clearInterval(phaseTimerInterval);
    set({ phaseElapsed: 0, timerRunning: true });
    phaseTimerInterval = setInterval(() => {
      get().tickPhaseTimer();
    }, 1000);
  },

  tickPhaseTimer: () => {
    const { phaseElapsed } = get();
    set({ phaseElapsed: phaseElapsed + 1 });
  },

  pauseTimer: () => {
    if (phaseTimerInterval) clearInterval(phaseTimerInterval);
    set({ timerRunning: false });
  },

  setTotalScore: (score) => set({ totalScore: score }),

  setStatus: (status) => {
    if (status === 'completed') {
      if (phaseTimerInterval) clearInterval(phaseTimerInterval);
      if (elapsedInterval) clearInterval(elapsedInterval);
      set({ timerRunning: false });
    }
    set({ status });
  },

  incrementTotalElapsed: () => set((state) => ({ totalElapsed: state.totalElapsed + 1 })),

  setIncludeInLog: (include) => set({ includeInLog: include }),

  setSaveToRecord: (save) => set({ saveToRecord: save }),

  reset: () => {
    if (phaseTimerInterval) clearInterval(phaseTimerInterval);
    if (elapsedInterval) clearInterval(elapsedInterval);
    set(initialState);
  },
}));
