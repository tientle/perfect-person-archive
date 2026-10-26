const overlapToggle = document.querySelector('#overlap-toggle');
const chunkViz = document.querySelector('.case-chunk-viz');
const overlapDescription = document.querySelector('#overlap-description');
if (overlapToggle && chunkViz && overlapDescription) {
  overlapToggle.addEventListener('click', () => {
    const overlapOn = overlapToggle.getAttribute('aria-pressed') !== 'true';
    overlapToggle.setAttribute('aria-pressed', String(overlapOn));
    overlapToggle.textContent = `Overlap: ${overlapOn ? 'on' : 'off'}`;
    chunkViz.classList.toggle('no-overlap', !overlapOn);
    overlapDescription.textContent = overlapOn
      ? 'With overlap, the ending of Chunk A appears again at the start of Chunk B. Diagram is illustrative, not to scale.'
      : 'Without overlap, each word belongs to just one chunk, so context around the boundary may be split. Diagram is illustrative, not to scale.';
  });
}
