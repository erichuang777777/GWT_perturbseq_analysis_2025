# Website demo recording package

This package turns the portal's existing demo drafts into a page-by-page recording plan.

- `STORYBOARD.md` defines the 3-minute narrative arc, timing, and browser actions.
- `SCRIPT.md` provides Traditional Chinese voice-over copy and explains why each screen matters.
- `screenshots/` contains 16 Playwright captures at 1920 × 1080.

The plan combines two existing repo drafts:

- `docs/mvp-research/pipeline/blindspot_fixes/USER_TEST_SCRIPT.md` supplies the researcher and clinical-evidence user journeys.
- `frontend/webserver/src/views/Deck.tsx` supplies the project-level story: scale, guardrails, preliminary outputs, and provenance.

## Recording guardrails

- Say “research-use target prioritisation” rather than “clinical recommendation.”
- Keep the two funnels parallel: the portal readiness path ends at 302 advance-ready targets; the publication delivery-decision path ends at 39 targets with a known modality.
- Define Core-5 as the intersection of the independent 15-gene primary-outcome shortlist and the publication set of 39.
- Describe the individual expression comparison as local, de-identified, and hypothesis-generating. It is not diagnosis, treatment selection, or efficacy prediction.
- Treat concept-module membership as descriptive. It never feeds the readiness call.

## Using your own voice

Playwright records the browser video but does not capture microphone audio. Record the narration separately with OBS, Audacity, Voice Memos, or another recorder, then combine it with the silent browser recording. The 3-minute script is intentionally divided into short timed blocks so each paragraph can be recorded as a separate take.

Recommended workflow:

1. Record the silent browser walkthrough at 1920 × 1080.
2. Read `SCRIPT.md` into a microphone as separate timed clips.
3. Remove long breaths and background noise, but keep the natural voice.
4. Merge the tracks with an editor, or with FFmpeg:

   ```bash
   ffmpeg -i site-demo-silent.webm -i narration.wav -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest site-demo-with-voice.mp4
   ```

## Screenshot index

1. [Home](screenshots/01-home.png)
2. [Target Explorer](screenshots/02-target-explorer.png)
3. [PLCG1 target dossier](screenshots/03-target-dossier-plcg1.png)
4. [Core-5 comparison](screenshots/04-core5-compare.png)
5. [Clinical scope and guardrails](screenshots/05-clinical-scope.png)
6. [Clinical Core-5 evidence matrix](screenshots/06-clinical-core5.png)
7. [Individual concept profile](screenshots/07-clinical-concept.png)
8. [Disease × drug evidence](screenshots/08-clinical-disease-drug.png)
9. [Population genetics](screenshots/09-clinical-popgen.png)
10. [Expression-feature comparison result](screenshots/10-clinical-expression-compare.png)
11. [Interactive figures](screenshots/11-interactive-figures.png)
12. [Figure and structure gallery](screenshots/12-figure-gallery.png)
13. [Docs and references](screenshots/13-docs.png)
14. [REST API](screenshots/14-api-docs.png)
15. [Four-slide overview](screenshots/15-overview-deck.png)
16. [Provenance](screenshots/16-provenance.png)
