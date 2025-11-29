# Frontend Design Skill

When generating frontend code, avoid "distributional convergence" toward generic AI aesthetics. Apply these principles to create distinctive, high-quality interfaces.

## Typography

**AVOID:** Inter, Roboto, system-ui, generic sans-serif fonts. These are overused in AI-generated designs.

**USE distinctive fonts:**
- **Code aesthetic:** JetBrains Mono, Fira Code, Space Mono
- **Technical:** IBM Plex Sans, Space Grotesk, Outfit
- **Editorial:** Playfair Display, Bricolage Grotesque, Sora
- **Modern:** Geist, Cal Sans, Satoshi

**Weight pairing:** Use extreme contrasts (100 vs 900, not 400 vs 600). Headlines should be BOLD.

**Scale:** Don't be afraid of large text. Hero headlines can be `text-7xl` to `text-9xl`.

## Color Schemes

**AVOID:** Generic blue primaries, purple gradients, standard shadcn defaults.

**Commit to a cohesive theme:**
- **Cyber-clean:** Deep slate backgrounds + electric cyan/teal primary + vibrant orange accent
- **Terminal:** Near-black background + green/amber monochrome + high contrast
- **Editorial:** Off-white/cream + black + single accent color
- **Neon:** Dark backgrounds + multiple vibrant neons (pink, cyan, yellow)

**Use dominant colors with sharp accents** rather than evenly distributed palettes. One primary, one accent, strong contrast.

## Backgrounds & Depth

**AVOID:** Solid colors, simple `bg-gradient-to-b from-background to-secondary/20`.

**Layer multiple effects:**
```css
/* Multi-layer gradient */
.gradient-bg {
  background:
    radial-gradient(ellipse at top, hsl(var(--primary) / 0.15), transparent 50%),
    radial-gradient(ellipse at bottom right, hsl(var(--accent) / 0.1), transparent 50%),
    hsl(var(--background));
}

/* Grid pattern overlay */
.grid-pattern {
  background-image: linear-gradient(hsl(var(--foreground) / 0.03) 1px, transparent 1px),
    linear-gradient(90deg, hsl(var(--foreground) / 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
}

/* Noise texture */
.noise-texture::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,..."); /* SVG noise */
  opacity: 0.3;
  pointer-events: none;
}
```

**Card effects:** Glow borders on hover, backdrop blur, semi-transparent backgrounds.

## Motion & Animation

**AVOID:** No animations, or scattered micro-interactions.

**Focus on high-impact moments:**
```css
/* Staggered entrance */
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in-up { animation: fade-in-up 0.6s ease-out forwards; }
.animate-delay-100 { animation-delay: 100ms; }
.animate-delay-200 { animation-delay: 200ms; }
.animate-delay-300 { animation-delay: 300ms; }
```

**Hover states:** Scale (1.02-1.05), shadow transitions, glow effects.

## Component Patterns

**Cards:**
- Use `rounded-xl` or `rounded-2xl`, not `rounded-md`
- Add ring/border with low opacity: `ring-2 ring-primary/20`
- Backdrop blur: `backdrop-blur-sm bg-card/50`
- Hover glow: `shadow-lg shadow-primary/10`

**Buttons:**
- Bold font weights: `font-semibold` or `font-bold`
- Colored shadows: `shadow-lg shadow-primary/20`
- Hover scale: `hover:scale-105`
- Larger padding for CTAs: `px-8 py-6` or `px-10 py-7`

**Icons:**
- Wrap in colored containers: gradient backgrounds with rings
- Larger sizes for feature sections: `w-8 h-8` in `w-16 h-16` containers

**Numbers/Stats:**
- Use monospace font (JetBrains Mono)
- `tabular-nums` for alignment
- Large, bold: `text-4xl font-black`

## Checklist Before Generating

1. [ ] Did I choose a distinctive font (not Inter/Roboto)?
2. [ ] Did I commit to a cohesive color theme?
3. [ ] Did I add layered backgrounds (gradients + patterns)?
4. [ ] Did I add entrance animations with staggered delays?
5. [ ] Did I use bold typography with extreme weight contrasts?
6. [ ] Did I add hover effects with glow/scale/shadow?
7. [ ] Does this look like a premium tool (Linear/Vercel/Raycast aesthetic)?

## Reference Implementations

**Dark tech dashboard:**
- Font: Space Grotesk + JetBrains Mono
- Primary: `hsl(187 96% 42%)` (electric cyan)
- Accent: `hsl(24 95% 53%)` (vibrant orange)
- Background: `hsl(222 47% 6%)` (deep navy)
- Effects: Animated gradients, grid overlay, noise texture, card glows

**Light editorial:**
- Font: Bricolage Grotesque + Inter (for body only)
- Primary: `hsl(0 0% 9%)` (near black)
- Accent: `hsl(12 76% 61%)` (coral)
- Background: `hsl(40 33% 98%)` (warm off-white)
- Effects: Subtle shadows, minimal animations, focus on typography
