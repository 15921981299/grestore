import fs from 'node:fs';
import path from 'node:path';
import lessons from '@/data/gre/lessons.json';

export interface GreLesson {
  id: number;
  slug: string;
  title: string;
  titleZh: string;
}

export interface GreVocabEntry {
  word: string;
  phonetic?: string | null;
  lines: string[];
}

export interface GreLessonContent {
  storyEn: string[];
  storyZh: string[];
  vocabulary?: GreVocabEntry[];
}

export const greLessons = lessons as GreLesson[];

export function getLessonBySlug(slug: string): GreLesson | undefined {
  return greLessons.find((lesson) => lesson.slug === slug);
}

export async function getLessonContent(id: number): Promise<GreLessonContent | null> {
  const files = import.meta.glob<GreLessonContent>('../data/gre/content/*.json');
  const key = Object.keys(files).find((entry) =>
    entry.endsWith(`/${formatLessonId(id)}.json`),
  );
  if (!key) return null;
  const loader = files[key];
  return loader ? loader() : null;
}

export function formatLessonId(id: number): string {
  return String(id).padStart(3, '0');
}

export function getAudioPath(id: number): string {
  return `/audio/${formatLessonId(id)}.mp3`;
}

export function hasLocalAudio(id: number): boolean {
  const localPath = path.join(process.cwd(), 'public', getAudioPath(id).replace(/^\//, ''));
  return fs.existsSync(localPath);
}

export function lessonHref(lesson: GreLesson): string {
  return `/lessons/${lesson.slug}/`;
}
