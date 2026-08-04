import type { ReactNode } from "react";

import { PublicFooter } from "@/components/public/public-footer";
import { PublicHeader } from "@/components/public/public-header";
import { SkipLink } from "@/components/ui/skip-link";
import type {
  PublicFooterData,
  PublicNavigationData,
  PublicSiteSettingsData,
} from "@/generated/api/src/models";
import { getPublicNavigation, getPublicSite } from "@/features/site-configuration/public-api";

// Keep the route eligible for runtime regeneration even when the API is not
// reachable during a production image build and the resilient fallback renders.
export const revalidate = 60;

const emptyNavigation: PublicNavigationData = { items: [] };
const emptyFooter: PublicFooterData = { columns: [] };

async function shellData(): Promise<{
  navigation: PublicNavigationData;
  site?: PublicSiteSettingsData;
}> {
  try {
    const [site, navigation] = await Promise.all([getPublicSite(), getPublicNavigation()]);
    return { navigation, site };
  } catch {
    return { navigation: emptyNavigation };
  }
}

export default async function PublicLayout({ children }: Readonly<{ children: ReactNode }>) {
  const { navigation, site } = await shellData();
  const brand = site?.websiteName;
  return (
    <div className="public-shell" lang={site?.defaultLocale ?? "en"}>
      <SkipLink href="#main-content" label="Skip to main content" />
      <PublicHeader
        {...(brand === undefined ? {} : { brand })}
        {...(site?.logoMediaId === undefined ? {} : { logoMediaId: site.logoMediaId })}
        navigation={navigation.items}
      />
      <main className="public-main" id="main-content" tabIndex={-1}>
        {children}
      </main>
      <PublicFooter
        {...(brand === undefined ? {} : { brand })}
        footer={site?.footer ?? emptyFooter}
      />
    </div>
  );
}
