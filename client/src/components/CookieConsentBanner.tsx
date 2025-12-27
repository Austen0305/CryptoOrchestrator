import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Cookie, X, Settings } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "wouter";

interface CookiePreferences {
  necessary: boolean;
  analytics: boolean;
  marketing: boolean;
}

export function CookieConsentBanner(): JSX.Element | null {
  const { t } = useTranslation();
  const [showBanner, setShowBanner] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [preferences, setPreferences] = useState<CookiePreferences>({
    necessary: true, // Always true, cannot be disabled
    analytics: false,
    marketing: false,
  });

  useEffect(() => {
    // Check if user has already made a choice
    const consent = localStorage.getItem("cookie-consent");
    if (!consent) {
      // Show banner after a short delay
      const timer = setTimeout(() => setShowBanner(true), 1000);
      return () => clearTimeout(timer);
    } else {
      // Load saved preferences
      try {
        const saved = JSON.parse(consent);
        setPreferences(saved);
      } catch (e) {
        // Invalid saved data, show banner again
        setShowBanner(true);
      }
      return undefined;
    }
  }, []);

  const handleAcceptAll = () => {
    const allAccepted: CookiePreferences = {
      necessary: true,
      analytics: true,
      marketing: true,
    };
    savePreferences(allAccepted);
    setShowBanner(false);
  };

  const handleRejectAll = () => {
    const onlyNecessary: CookiePreferences = {
      necessary: true,
      analytics: false,
      marketing: false,
    };
    savePreferences(onlyNecessary);
    setShowBanner(false);
  };

  const handleSavePreferences = () => {
    savePreferences(preferences);
    setShowSettings(false);
    setShowBanner(false);
  };

  const savePreferences = (prefs: CookiePreferences) => {
    localStorage.setItem("cookie-consent", JSON.stringify(prefs));
    localStorage.setItem("cookie-consent-date", new Date().toISOString());
    
    // Set analytics cookie if enabled
    if (prefs.analytics) {
      document.cookie = "analytics-enabled=true; path=/; max-age=31536000"; // 1 year
    } else {
      document.cookie = "analytics-enabled=false; path=/; max-age=31536000";
    }
    
    // Set marketing cookie if enabled
    if (prefs.marketing) {
      document.cookie = "marketing-enabled=true; path=/; max-age=31536000";
    } else {
      document.cookie = "marketing-enabled=false; path=/; max-age=31536000";
    }

    // Trigger custom event for analytics initialization
    window.dispatchEvent(new CustomEvent("cookie-consent-updated", { detail: prefs }));
  };

  const handleOpenSettings = () => {
    setShowSettings(true);
  };

  if (!showBanner && !showSettings) {
    return null;
  }

  if (showSettings) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cookie className="h-5 w-5" />
                <CardTitle>{t("cookieConsent.settings.title", "Cookie Settings")}</CardTitle>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowSettings(false)}
                aria-label={t("cookieConsent.close", "Close")}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <CardDescription>
              {t(
                "cookieConsent.settings.description",
                "Manage your cookie preferences. You can enable or disable different types of cookies below."
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Necessary Cookies */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">
                    {t("cookieConsent.necessary.title", "Necessary Cookies")}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {t(
                      "cookieConsent.necessary.description",
                      "These cookies are essential for the website to function properly. They cannot be disabled."
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">
                    {t("cookieConsent.alwaysEnabled", "Always On")}
                  </span>
                </div>
              </div>
            </div>

            {/* Analytics Cookies */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold">
                    {t("cookieConsent.analytics.title", "Analytics Cookies")}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {t(
                      "cookieConsent.analytics.description",
                      "These cookies help us understand how visitors interact with our website by collecting and reporting information anonymously."
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant={preferences.analytics ? "default" : "outline"}
                    size="sm"
                    onClick={() =>
                      setPreferences({ ...preferences, analytics: !preferences.analytics })
                    }
                  >
                    {preferences.analytics
                      ? t("cookieConsent.enabled", "Enabled")
                      : t("cookieConsent.disabled", "Disabled")}
                  </Button>
                </div>
              </div>
            </div>

            {/* Marketing Cookies */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold">
                    {t("cookieConsent.marketing.title", "Marketing Cookies")}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {t(
                      "cookieConsent.marketing.description",
                      "These cookies are used to deliver personalized advertisements and track campaign performance."
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant={preferences.marketing ? "default" : "outline"}
                    size="sm"
                    onClick={() =>
                      setPreferences({ ...preferences, marketing: !preferences.marketing })
                    }
                  >
                    {preferences.marketing
                      ? t("cookieConsent.enabled", "Enabled")
                      : t("cookieConsent.disabled", "Disabled")}
                  </Button>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t">
              <div className="flex flex-col sm:flex-row gap-2 justify-end">
                <Button variant="outline" onClick={() => setShowSettings(false)}>
                  {t("cookieConsent.cancel", "Cancel")}
                </Button>
                <Button onClick={handleSavePreferences}>
                  {t("cookieConsent.savePreferences", "Save Preferences")}
                </Button>
              </div>
            </div>

            <div className="pt-4 border-t text-sm text-muted-foreground">
              <p>
                {t("cookieConsent.learnMore", "Learn more about our use of cookies in our")}{" "}
                <Link
                  href="/legal/cookie-policy"
                  className="text-primary hover:underline"
                >
                  {t("cookieConsent.cookiePolicy", "Cookie Policy")}
                </Link>
                .
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-background border-t shadow-lg"
      role="banner"
      aria-label={t("cookieConsent.banner", "Cookie Consent Banner")}
    >
      <div className="max-w-7xl mx-auto">
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
              <div className="flex items-start gap-3 flex-1">
                <Cookie className="h-5 w-5 mt-0.5 text-primary" />
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">
                    {t("cookieConsent.title", "We use cookies")}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {t(
                      "cookieConsent.description",
                      "We use cookies to enhance your browsing experience, analyze site traffic, and personalize content. By clicking 'Accept All', you consent to our use of cookies."
                    )}{" "}
                    <Link
                      href="/legal/cookie-policy"
                      className="text-primary hover:underline"
                    >
                      {t("cookieConsent.learnMore", "Learn more")}
                    </Link>
                    .
                  </p>
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-2 w-full md:w-auto">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleOpenSettings}
                  className="flex items-center gap-2"
                >
                  <Settings className="h-4 w-4" />
                  {t("cookieConsent.customize", "Customize")}
                </Button>
                <Button variant="outline" size="sm" onClick={handleRejectAll}>
                  {t("cookieConsent.rejectAll", "Reject All")}
                </Button>
                <Button size="sm" onClick={handleAcceptAll}>
                  {t("cookieConsent.acceptAll", "Accept All")}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

