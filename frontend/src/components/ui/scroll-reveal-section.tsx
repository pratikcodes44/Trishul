"use client";

import { motion, useReducedMotion } from "framer-motion";
import { ReactNode } from "react";

interface ScrollRevealSectionProps {
  children: ReactNode;
  className?: string;
  staggerChildren?: number;
}

export function ScrollRevealSection({
  children,
  className,
  staggerChildren = 0.07,
}: ScrollRevealSectionProps) {
  const reduced = useReducedMotion();

  if (reduced) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.4 }}
      variants={{
        hidden: {},
        visible: {
          transition: {
            staggerChildren,
          },
        },
      }}
    >
      {children}
    </motion.div>
  );
}

export function ScrollRevealItem({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  const reduced = useReducedMotion();

  if (reduced) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      variants={{
        hidden: { opacity: 0, y: 12 },
        visible: {
          opacity: 1,
          y: 0,
          transition: {
            duration: 0.22,
            ease: "easeOut",
          },
        },
      }}
    >
      {children}
    </motion.div>
  );
}
