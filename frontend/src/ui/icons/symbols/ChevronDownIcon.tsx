import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const ChevronDownIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="chevronDown"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const rotation = !isReduced && isActive ? "rotate(180deg)" : "rotate(0deg)";
      return (
        <path
          d="m6 9 6 6 6-6"
          style={{
            transform: rotation,
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 160ms ${MOTION_EASINGS.standard}`
          }}
        />
      );
    }}
  />
);
