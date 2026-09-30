"use client";

import { useState } from "react";

import { api, ApiError } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input, Label, Textarea } from "@/components/ui/Fields";
import { InlineError } from "@/components/ui/States";
import { TAG_COLORS, formatDateTime } from "@/lib/format";
import type { Note, Tag } from "@/lib/types";

export function TagsEditor({
  candidateId,
  tags,
  onChange,
}: {
  candidateId: number;
  tags: Tag[];
  onChange: () => void;
}) {
  const [name, setName] = useState("");
  const [color, setColor] = useState("slate");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function addTag(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api.candidates.addTag(candidateId, { name: name.trim(), color });
      setName("");
      onChange();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add the tag.");
    } finally {
      setBusy(false);
    }
  }

  async function removeTag(tagId: number) {
    setBusy(true);
    setError(null);
    try {
      await api.candidates.removeTag(candidateId, tagId);
      onChange();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not remove the tag.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-1.5">
        {tags.length === 0 ? (
          <p className="text-sm text-slate-500">No tags yet.</p>
        ) : (
          tags.map((tag) => (
            <span key={tag.id} className="inline-flex items-center gap-1">
              <Badge className={TAG_COLORS[tag.color] ?? TAG_COLORS.slate}>{tag.name}</Badge>
              <button
                type="button"
                aria-label={`Remove tag ${tag.name}`}
                disabled={busy}
                onClick={() => removeTag(tag.id)}
                className="text-xs text-slate-500 hover:text-rose-600"
              >
                ×
              </button>
            </span>
          ))
        )}
      </div>
      <form onSubmit={addTag} className="flex items-end gap-2">
        <div className="flex-1">
          <Label htmlFor="tag-name">Add tag</Label>
          <Input
            id="tag-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. top-match"
          />
        </div>
        <select
          aria-label="Tag color"
          value={color}
          onChange={(event) => setColor(event.target.value)}
          className="rounded-lg border-0 bg-white px-2 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300"
        >
          {Object.keys(TAG_COLORS).map((key) => (
            <option key={key} value={key}>
              {key}
            </option>
          ))}
        </select>
        <Button type="submit" variant="secondary" size="sm" loading={busy}>
          Add
        </Button>
      </form>
      {error ? <InlineError message={error} /> : null}
    </div>
  );
}

export function NotesPanel({
  candidateId,
  notes,
  onChange,
}: {
  candidateId: number;
  notes: Note[];
  onChange: () => void;
}) {
  const [body, setBody] = useState("");
  const [author, setAuthor] = useState("Recruiter");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function addNote(event: React.FormEvent) {
    event.preventDefault();
    if (!body.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api.candidates.addNote(candidateId, { body: body.trim(), author });
      setBody("");
      onChange();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save the note.");
    } finally {
      setBusy(false);
    }
  }

  async function deleteNote(noteId: number) {
    setBusy(true);
    setError(null);
    try {
      await api.candidates.deleteNote(candidateId, noteId);
      onChange();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete the note.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <form onSubmit={addNote} className="space-y-2">
        <Textarea
          rows={3}
          value={body}
          onChange={(event) => setBody(event.target.value)}
          placeholder="Add a recruiter note…"
          aria-label="Note text"
        />
        <div className="flex items-center gap-2">
          <Input
            value={author}
            onChange={(event) => setAuthor(event.target.value)}
            aria-label="Note author"
            className="max-w-[140px]"
          />
          <Button type="submit" size="sm" loading={busy}>
            Save note
          </Button>
        </div>
      </form>
      {error ? <InlineError message={error} /> : null}

      <ul className="space-y-3">
        {notes.length === 0 ? (
          <li className="text-sm text-slate-500">No notes yet — add your first above.</li>
        ) : (
          notes.map((note) => (
            <li key={note.id} className="rounded-lg bg-slate-50 px-3 py-2.5">
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-medium text-slate-600">
                  {note.author} · {formatDateTime(note.created_at)}
                </p>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => deleteNote(note.id)}
                  className="text-xs text-slate-500 hover:text-rose-600"
                >
                  Delete
                </button>
              </div>
              <p className="mt-1 text-sm leading-relaxed text-slate-700">{note.body}</p>
            </li>
          ))
        )}
      </ul>
    </div>
  );
}
