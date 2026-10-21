import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const AttachFileIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="attachFile"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const tiltClip = !isReduced && isActive ? "rotate(10deg)" : "rotate(0deg)";
      return (
        <path
          d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l7.88-7.88"
          style={{
            transform: tiltClip,
            transformOrigin: "12px 12px",
            transition: isReduced ? "none" : `transform 180ms ${MOTION_EASINGS.standard}`
          }}
        />
      );
    }}
  />
);
