# Edit

How Jean's VSL gets put together. Nothing in here needs uploading; it's the editing setup.

- `scripts/transcribe.py`: word-level transcript of a video (Whisper large-v3-turbo), with an optional prompt of
  names and trading terms so they're heard right.
- `transcript.json`: Jean's raw video, every word with its start and end time. Made from two passes: the
  vocabulary-prompted one, plus the plain one for 1:13.9–1:52.4, where the prompted pass mislabelled Alpha Capital as
  FTMO and skipped 1:40–1:52. Times are in the raw video; the readable version is
  [`03-raw-vsl-footage/TRANSCRIPT.md`](../03-raw-vsl-footage/TRANSCRIPT.md).
