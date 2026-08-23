interface RingMarkProps {
  className?: string
}

/* Ring's brand mark: an ink-drawn circle, thin where the pen lands near the top
   left and swelling toward the bottom. The path matches
   public/assets/images/logo.svg, the source of the PWA icons; here the viewBox
   crops that 512 tile to the ring's bounding box so the mark fills the box it
   is given, and the fill follows currentColor instead of the tile's cream. */
export function RingMark({ className }: RingMarkProps) {
  return (
    <svg
      viewBox="90 90 332 332"
      fill="currentColor"
      aria-hidden="true"
      className={className}
    >
      <path
        transform="rotate(-16 256 256)"
        d="M 108.09 180.64 A 166 166 0 1 1 101.03 196.51 A 26.65 26.65 0 0 1 153.84 203.71 A 118 118 0 1 0 158.86 192.43 A 26.06 26.06 0 0 1 108.09 180.64 Z"
      />
    </svg>
  )
}
