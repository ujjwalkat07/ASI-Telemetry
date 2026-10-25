"use client";

import * as React from "react";
import {
  AlertCircle,
  Check,
  CheckCircle2,
  Copy,
  Eye,
  EyeOff,
  KeyRound,
  Lock,
  Save,
  Shield,
  ShieldCheck,
  User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { getStoredUser, updateUserProfile, AuthUser } from "@/lib/auth";

export default function SettingsPage() {
  const [user, setUser] = React.useState<AuthUser | null>(null);
  const [copiedId, setCopiedId] = React.useState(false);

  // Profile Name Form State
  const [name, setName] = React.useState("");
  const [isUpdatingName, setIsUpdatingName] = React.useState(false);
  const [nameSuccess, setNameSuccess] = React.useState<string | null>(null);
  const [nameError, setNameError] = React.useState<string | null>(null);

  // Password Form State
  const [currentPassword, setCurrentPassword] = React.useState("");
  const [newPassword, setNewPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [showCurrentPassword, setShowCurrentPassword] = React.useState(false);
  const [showNewPassword, setShowNewPassword] = React.useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = React.useState(false);
  const [isUpdatingPassword, setIsUpdatingPassword] = React.useState(false);
  const [passwordSuccess, setPasswordSuccess] = React.useState<string | null>(null);
  const [passwordError, setPasswordError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const current = getStoredUser();
    setUser(current);
    if (current?.name) {
      setName(current.name);
    }
  }, []);

  const handleCopyId = () => {
    if (!user?.id) return;
    navigator.clipboard.writeText(user.id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  const handleUpdateName = async (e: React.FormEvent) => {
    e.preventDefault();
    setNameSuccess(null);
    setNameError(null);

    const trimmed = name.trim();
    if (!trimmed || trimmed.length < 2) {
      setNameError("Name must contain at least 2 characters.");
      return;
    }

    if (trimmed === user?.name) {
      setNameError("Please enter a new name different from your current name.");
      return;
    }

    setIsUpdatingName(true);
    try {
      const result = await updateUserProfile({ name: trimmed });
      if (result.success && result.user) {
        setUser(result.user);
        setName(result.user.name);
        setNameSuccess("Display name updated successfully!");
        setTimeout(() => setNameSuccess(null), 4000);
      } else {
        setNameError(result.error || "Failed to update display name.");
      }
    } finally {
      setIsUpdatingName(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordSuccess(null);
    setPasswordError(null);

    if (!currentPassword) {
      setPasswordError("Please enter your current password.");
      return;
    }

    if (!newPassword) {
      setPasswordError("Please enter a new password.");
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirmation password do not match.");
      return;
    }

    if (newPassword === currentPassword) {
      setPasswordError("New password must be different from your current password.");
      return;
    }

    setIsUpdatingPassword(true);
    try {
      const result = await updateUserProfile({
        currentPassword,
        newPassword,
      });

      if (result.success) {
        setPasswordSuccess("Password changed successfully! Next time you log in, use your new password.");
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
        setTimeout(() => setPasswordSuccess(null), 5000);
      } else {
        setPasswordError(result.error || "Failed to update password.");
      }
    } finally {
      setIsUpdatingPassword(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6 lg:p-10 space-y-8 max-w-5xl mx-auto w-full">
      {/* Page Header */}
      <div className="border-b border-border pb-6 space-y-1">
        <div className="flex items-center gap-2 text-primary font-medium text-xs tracking-wider uppercase">
          <Shield className="h-3.5 w-3.5" />
          <span>Account &amp; Security</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Profile &amp; Account Settings
        </h1>
        <p className="text-sm text-muted-foreground">
          Manage your account profile, personal display name, and login credentials.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {/* Section 1: Display Name & Profile Information */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-xs space-y-6">
          <div className="flex items-center justify-between border-b border-border pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary border border-primary/20">
                <User className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-foreground">
                  Personal Information
                </h2>
                <p className="text-xs text-muted-foreground">
                  Update your display name visible across telemetry agent traces and reports.
                </p>
              </div>
            </div>
            <Badge variant="outline" className="border-border text-xs gap-1.5">
              <ShieldCheck className="h-3 w-3 text-emerald-500" />
              Active Account
            </Badge>
          </div>

          {/* Feedback alerts */}
          {nameSuccess && (
            <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-xs text-emerald-400">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
              <span>{nameSuccess}</span>
            </div>
          )}

          {nameError && (
            <div className="flex items-center gap-2 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{nameError}</span>
            </div>
          )}

          <form onSubmit={handleUpdateName} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Display Name Input */}
              <div className="space-y-1.5">
                <label
                  htmlFor="display-name"
                  className="text-xs font-medium text-foreground flex items-center justify-between"
                >
                  <span>Display Name</span>
                  <span className="text-[10px] text-muted-foreground font-normal">
                    Min 2 characters
                  </span>
                </label>
                <Input
                  id="display-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Satoshi Nakamoto"
                  className="h-9 text-xs"
                  required
                />
              </div>

              {/* Email Address (Read-only) */}
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-foreground flex items-center justify-between">
                  <span>Email Address</span>
                  <span className="text-[10px] text-emerald-400 flex items-center gap-1">
                    <Check className="h-2.5 w-2.5" /> Verified
                  </span>
                </label>
                <Input
                  type="email"
                  value={user?.email || ""}
                  disabled
                  className="h-9 text-xs bg-muted/50 cursor-not-allowed opacity-80"
                />
              </div>
            </div>

            {/* Read-only account metadata row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/30 px-3 py-2 text-xs">
                <span className="text-muted-foreground">User ID:</span>
                <div className="flex items-center gap-2 font-mono text-[11px] text-foreground">
                  <span className="truncate max-w-[170px]" title={user?.id}>
                    {user?.id || "N/A"}
                  </span>
                  {user?.id && (
                    <button
                      type="button"
                      onClick={handleCopyId}
                      className="text-muted-foreground hover:text-foreground transition-colors"
                      title="Copy User ID"
                    >
                      {copiedId ? (
                        <Check className="h-3.5 w-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                    </button>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/30 px-3 py-2 text-xs">
                <span className="text-muted-foreground">Member Since:</span>
                <span className="font-mono text-[11px] text-foreground">
                  {user?.created_at
                    ? new Date(user.created_at).toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })
                    : "Active Member"}
                </span>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button
                type="submit"
                disabled={isUpdatingName || name.trim() === user?.name}
                size="sm"
                className="gap-2 text-xs font-medium"
              >
                {isUpdatingName ? (
                  <>
                    <div className="h-3 w-3 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Save className="h-3.5 w-3.5" />
                    <span>Save Name</span>
                  </>
                )}
              </Button>
            </div>
          </form>
        </div>

        {/* Section 2: Change Password & Credentials */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-xs space-y-6">
          <div className="flex items-center justify-between border-b border-border pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary border border-primary/20">
                <Lock className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-foreground">
                  Password &amp; Security
                </h2>
                <p className="text-xs text-muted-foreground">
                  Update the password used to sign in to your ASI-Telemetry dashboard.
                </p>
              </div>
            </div>
            <Badge variant="outline" className="border-border text-xs gap-1.5 font-mono">
              Argon2id Encrypted
            </Badge>
          </div>

          {/* Feedback alerts */}
          {passwordSuccess && (
            <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-xs text-emerald-400">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
              <span>{passwordSuccess}</span>
            </div>
          )}

          {passwordError && (
            <div className="flex items-center gap-2 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{passwordError}</span>
            </div>
          )}

          <form onSubmit={handleUpdatePassword} className="space-y-4">
            {/* Current Password Field */}
            <div className="space-y-1.5 max-w-md">
              <label
                htmlFor="current-password"
                className="text-xs font-medium text-foreground flex items-center justify-between"
              >
                <span>Current Password</span>
              </label>
              <div className="relative">
                <Input
                  id="current-password"
                  type={showCurrentPassword ? "text" : "password"}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter your current account password"
                  className="h-9 pr-9 text-xs"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showCurrentPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* New Password Field */}
              <div className="space-y-1.5">
                <label
                  htmlFor="new-password"
                  className="text-xs font-medium text-foreground flex items-center justify-between"
                >
                  <span>New Password</span>
                  <span className="text-[10px] text-muted-foreground font-normal">
                    Min 8 characters
                  </span>
                </label>
                <div className="relative">
                  <Input
                    id="new-password"
                    type={showNewPassword ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter strong new password"
                    className="h-9 pr-9 text-xs"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showNewPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Confirm Password Field */}
              <div className="space-y-1.5">
                <label
                  htmlFor="confirm-password"
                  className="text-xs font-medium text-foreground flex items-center justify-between"
                >
                  <span>Confirm New Password</span>
                  {newPassword && confirmPassword && (
                    <span
                      className={`text-[10px] flex items-center gap-1 ${
                        newPassword === confirmPassword
                          ? "text-emerald-400"
                          : "text-destructive"
                      }`}
                    >
                      {newPassword === confirmPassword ? (
                        <>
                          <Check className="h-2.5 w-2.5" /> Matches
                        </>
                      ) : (
                        "Does not match"
                      )}
                    </span>
                  )}
                </label>
                <div className="relative">
                  <Input
                    id="confirm-password"
                    type={showConfirmPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter new password"
                    className="h-9 pr-9 text-xs"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Password security guidelines checklist */}
            <div className="rounded-lg border border-border/70 bg-muted/20 p-3 space-y-1.5 text-xs text-muted-foreground">
              <span className="font-medium text-foreground text-[11px] block">
                Security Recommendations:
              </span>
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1 text-[11px]">
                <li className="flex items-center gap-1.5">
                  <span className={`h-1.5 w-1.5 rounded-full ${newPassword.length >= 8 ? "bg-emerald-500" : "bg-muted-foreground"}`} />
                  At least 8 characters long
                </li>
                <li className="flex items-center gap-1.5">
                  <span className={`h-1.5 w-1.5 rounded-full ${/[A-Z]/.test(newPassword) ? "bg-emerald-500" : "bg-muted-foreground"}`} />
                  Includes uppercase letters
                </li>
                <li className="flex items-center gap-1.5">
                  <span className={`h-1.5 w-1.5 rounded-full ${/[0-9]/.test(newPassword) ? "bg-emerald-500" : "bg-muted-foreground"}`} />
                  Includes numbers or symbols
                </li>
                <li className="flex items-center gap-1.5">
                  <span className={`h-1.5 w-1.5 rounded-full ${newPassword && newPassword !== currentPassword ? "bg-emerald-500" : "bg-muted-foreground"}`} />
                  Different from current password
                </li>
              </ul>
            </div>

            <div className="flex justify-end pt-2">
              <Button
                type="submit"
                disabled={
                  isUpdatingPassword ||
                  !currentPassword ||
                  !newPassword ||
                  newPassword.length < 8 ||
                  newPassword !== confirmPassword
                }
                size="sm"
                className="gap-2 text-xs font-medium"
              >
                {isUpdatingPassword ? (
                  <>
                    <div className="h-3 w-3 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                    <span>Updating Password...</span>
                  </>
                ) : (
                  <>
                    <KeyRound className="h-3.5 w-3.5" />
                    <span>Update Password</span>
                  </>
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
