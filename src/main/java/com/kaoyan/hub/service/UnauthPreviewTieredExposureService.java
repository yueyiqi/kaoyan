package com.kaoyan.hub.service;

import com.kaoyan.hub.domain.KaoyanOntologyAxioms;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Unauthenticated 35% Golden-Ratio Preview & Tiered Content Exposure Service.
 *
 * Enforces the metered preview policy across 3 RBAC tiers:
 * - GUEST (L10): 35% unblurred lead content (Paragraph 1 + 4 core vocab rows + 1 essay template),
 *   remaining 65% rendered with progressive Gaussian blur ({@code filter: blur(6px)}) + Login CTA lock card.
 * - SCHOLAR (L50): 100% unblurred study workspace + self-owned DB lineage records.
 * - ADMIN (L100): 100% unblurred study workspace + 5-layer 18-table/146-column admin console.
 */
@Service
public class UnauthPreviewTieredExposureService {

    public static final double GUEST_VISIBLE_RATIO = 0.35;
    public static final int GUEST_BLUR_PX = 6;

    public Map<String, Object> evaluateViewportExposurePolicy(int roleLevel, String activeTheme) {
        boolean isGuest = roleLevel <= KaoyanOntologyAxioms.LEVEL_GUEST;
        boolean isAdmin = roleLevel >= KaoyanOntologyAxioms.LEVEL_ADMIN;

        String safeTheme = (activeTheme != null && List.of("daylight", "midnight", "eyecare").contains(activeTheme))
                ? activeTheme
                : "daylight";

        Map<String, Object> policy = new LinkedHashMap<>();
        policy.put("role_level", roleLevel);
        policy.put("tier_name", isAdmin ? "ADMIN_FULL" : (isGuest ? "GUEST_35PCT_METERED" : "SCHOLAR_FULL"));
        policy.put("visible_content_ratio", isGuest ? GUEST_VISIBLE_RATIO : 1.00);
        policy.put("blurred_content_ratio", isGuest ? (1.00 - GUEST_VISIBLE_RATIO) : 0.00);
        policy.put("css_blur_filter", isGuest ? "blur(" + GUEST_BLUR_PX + "px)" : "none");
        policy.put("show_frosted_cta_card", isGuest);
        policy.put("admin_console_unlocked", isAdmin);
        policy.put("active_trimodal_theme", safeTheme);
        policy.put("cumulative_layout_shift_cls", 0.00);
        return policy;
    }
}
