import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const FallbackCatalogIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="fallback"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      return (
        <g
          style={{
            transform: !isReduced && isActive ? "scale(1.05)" : "scale(1)",
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 180ms ${MOTION_EASINGS.standard}`
          }}
        >
          <circle cx="12" cy="12" r="10" />
          <circle cx="12" cy="12" r="4" />
        </g>
      );
    }}
  />
);
