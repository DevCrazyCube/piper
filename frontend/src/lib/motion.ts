import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";

const reduced = () =>
  typeof window !== "undefined" &&
  window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

/** Stagger child [data-anim] elements in on mount (fade + rise, eased). */
export function useEntrance<T extends HTMLElement = HTMLDivElement>() {
  const ref = useRef<T>(null);
  useEffect(() => {
    if (!ref.current || reduced()) return;
    const els = ref.current.querySelectorAll("[data-anim]");
    const ctx = gsap.context(() => {
      gsap.from(els, { opacity: 0, y: 16, duration: 0.5, stagger: 0.05, ease: "expo.out" });
    }, ref);
    return () => ctx.revert();
  }, []);
  return ref;
}

/** Drift the ambient aurora blobs forever (subtle). */
export function useAurora() {
  useEffect(() => {
    if (reduced()) return;
    const ctx = gsap.context(() => {
      gsap.to(".aurora.a", { x: 80, y: 60, duration: 22, repeat: -1, yoyo: true, ease: "sine.inOut" });
      gsap.to(".aurora.b", { x: -70, y: -40, duration: 26, repeat: -1, yoyo: true, ease: "sine.inOut" });
    });
    return () => ctx.revert();
  }, []);
}

/** Travelling pulses along the pipeline connectors. */
export function usePipelinePulses(deps: unknown[] = []) {
  useEffect(() => {
    if (reduced()) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(".stage .flow .pulse",
        { left: 0, opacity: 0 },
        { left: 14, opacity: 1, duration: 1.1, repeat: -1, stagger: 0.12, ease: "power1.inOut" });
    });
    return () => ctx.revert();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}

/** Count a number up from 0 on mount. */
export function useCountUp(target: number, decimals = 0) {
  const [val, setVal] = useState(reduced() ? target : 0);
  useEffect(() => {
    if (reduced()) { setVal(target); return; }
    const obj = { v: 0 };
    const tw = gsap.to(obj, {
      v: target, duration: 1.1, ease: "power2.out",
      onUpdate: () => setVal(obj.v),
    });
    return () => { tw.kill(); };
  }, [target]);
  return decimals ? val.toFixed(decimals) : Math.round(val).toLocaleString();
}
