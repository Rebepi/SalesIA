import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const SunIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="sun"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const rotateSun = !isReduced && isActive ? "rotate(45deg)" : "rotate(0deg)";
      return (
        <g
          style={{
            transform: rotateSun,
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 200ms ${MOTION_EASINGS.standard}`
          }}
        >
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
        </g>
      );
    }}
  />
);
