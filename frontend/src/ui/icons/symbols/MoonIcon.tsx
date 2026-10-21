import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const MoonIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="moon"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const rotateMoon = !isReduced && isActive ? "rotate(15deg)" : "rotate(0deg)";
      return (
        <path
          d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"
          style={{
            transform: rotateMoon,
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 200ms ${MOTION_EASINGS.standard}`
          }}
        />
      );
    }}
  />
);
