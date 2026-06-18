// 高考场景枚举常量

export const GRADE_LEVELS = [
  { label: '高中', value: '高中' },
  { label: '初中', value: '初中' },
  { label: '高一', value: '高一' },
  { label: '高二', value: '高二' },
  { label: '高三', value: '高三' },
] as const;

export const DEFAULT_GRADE_LEVEL = '高中';

// 高考作文五大题型
export const TOPIC_TYPES = [
  { label: '材料作文', value: '材料作文' },
  { label: '命题作文', value: '命题作文' },
  { label: '话题作文', value: '话题作文' },
  { label: '任务驱动型作文', value: '任务驱动型作文' },
  { label: '看图作文', value: '看图作文' },
] as const;

export const DEFAULT_TOPIC_TYPE = '材料作文';

// 文体（高考以议论文为主）
export const WRITING_STYLES = [
  { label: '议论文', value: '议论文' },
  { label: '记叙文', value: '记叙文' },
  { label: '散文', value: '散文' },
  { label: '小说', value: '小说' },
] as const;

export const DEFAULT_STYLE = '议论文';

// 字数
export const WORD_COUNTS = [
  { label: '600字', value: 600 },
  { label: '800字（标准）', value: 800 },
  { label: '1000字', value: 1000 },
] as const;

export const DEFAULT_WORD_COUNT = 800;

// 高考评分维度
export const SCORING_RUBRIC_OPTIONS = [
  { label: '内容立意', value: '内容立意' },
  { label: '结构安排', value: '结构安排' },
  { label: '语言表达', value: '语言表达' },
  { label: '发展等级', value: '发展等级' },
] as const;

export const DEFAULT_SCORING_RUBRIC = ['内容立意', '结构安排', '语言表达', '发展等级'];

// 写作辅助类型
export const HELP_TYPES = [
  { label: '润色优化', value: 'polish' as const, icon: 'EditOutlined' },
  { label: '续写建议', value: 'continue' as const, icon: 'PlayCircleOutlined' },
  { label: '修辞建议', value: 'rhetoric' as const, icon: 'HighlightOutlined' },
  { label: '过渡衔接', value: 'transition' as const, icon: 'SwapOutlined' },
] as const;

// 搜索过滤 - 文档类型
export const DOC_CATEGORIES = [
  { label: '范文', value: '范文' },
  { label: '素材', value: '素材' },
  { label: '技巧', value: '技巧' },
  { label: '解析', value: '解析' },
  { label: '综合', value: '综合' },
  { label: '真题', value: '真题' },
] as const;

// 题型
export const QUESTION_TYPES = [
  { label: '作文', value: '作文' },
  { label: '现代文阅读', value: '现代文阅读' },
  { label: '文言文阅读', value: '文言文阅读' },
  { label: '古诗词鉴赏', value: '古诗词鉴赏' },
  { label: '名句默写', value: '名句默写' },
  { label: '语言运用', value: '语言运用' },
  { label: '综合', value: '综合' },
] as const;

// 考区
export const EXAM_REGIONS = [
  { label: '全国甲卷', value: '全国甲卷' },
  { label: '全国乙卷', value: '全国乙卷' },
  { label: '全国新高考I卷', value: '全国新高考I卷' },
  { label: '全国新高考II卷', value: '全国新高考II卷' },
  { label: '北京', value: '北京' },
  { label: '上海', value: '上海' },
  { label: '天津', value: '天津' },
  { label: '浙江', value: '浙江' },
  { label: '江苏', value: '江苏' },
  { label: '山东', value: '山东' },
  { label: '广东', value: '广东' },
  { label: '湖南', value: '湖南' },
  { label: '湖北', value: '湖北' },
  { label: '四川', value: '四川' },
  { label: '重庆', value: '重庆' },
] as const;

// 科目
export const SUBJECTS = [
  { label: '语文', value: '语文' },
  { label: '数学', value: '数学' },
  { label: '英语', value: '英语' },
] as const;

// 来源类型
export const SOURCE_TYPES = [
  { label: '试卷', value: 'exam_paper' },
  { label: '资料库', value: '' },
] as const;

// === 强化训练 ===

export const PRACTICE_PHASES = [
  { key: 'topic_analysis', title: '审题分析', suggestedSeconds: 600 },
  { key: 'outline', title: '构思提纲', suggestedSeconds: 900 },
  { key: 'essay', title: '限时写作', suggestedSeconds: 2700 },
  { key: 'evaluation', title: 'AI 评估', suggestedSeconds: 0 },
] as const;

export const DEFAULT_ESSAY_TIME_LIMIT = 45; // 分钟
