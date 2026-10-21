import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const RefreshCwIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="refreshCw"
    renderPaths={(state, isReduced) => {
      const isLoading = state === "loading";
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const spin = !isReduced && isActive ? "rotate(180deg)" : "rotate(0deg)";
      return (
        <g
          className={isLoading && !isReduced ? "animate-spin" : ""}
          style={{
            transform: isLoading ? undefined : spin,
            transformOrigin: "12px 12px",
            transition: isReduced || isLoading ? "none" : `transform 240ms ${MOTION_EASINGS.standard}`
          }}
        >
          <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
          <path d="M21 3v5h-5" />
          <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
          <path d="M3 21v-5h5" />
        </g>
      );
    }}
  />
);
