import os


def patch_file(path, search_text, replace_text):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Normalize line endings for replacement
    content = content.replace(
        search_text.replace("\n", "\r\n"), replace_text.replace("\n", "\r\n")
    )
    content = content.replace(
        search_text.replace("\r\n", "\n"), replace_text.replace("\r\n", "\n")
    )

    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)


# ProfileScreen.tsx
profile_path = r"c:\Users\William Walker\Desktop\CryptoOrchestrator\mobile\src\screens\ProfileScreen.tsx"
search1 = """      const errorDetail =
        errorData?.detail ?? (error as Error).message;"""
replace1 = "      const errorDetail = errorData?.detail ?? (error as Error).message;"

search2 = '{profile?.username ?? profile?.email ?? "User"}'
replace2 = '{(profile?.username ?? profile?.email ?? "User")}'

patch_file(profile_path, search1, replace1)
patch_file(profile_path, search2, replace2)

# TradingScreen.tsx
trading_path = r"c:\Users\William Walker\Desktop\CryptoOrchestrator\mobile\src\screens\TradingScreen.tsx"
search3 = """      Alert.alert(
        "Trade Failed",
        errorData?.detail ?? (err as Error).message
      );"""
replace3 = (
    '      Alert.alert("Trade Failed", errorData?.detail ?? (err as Error).message);'
)

search4 = """      Alert.alert(
        "Swap Failed",
        errorData?.detail ?? (err as Error).message
      );"""
replace4 = (
    '      Alert.alert("Swap Failed", errorData?.detail ?? (err as Error).message);'
)

patch_file(trading_path, search3, replace3)
patch_file(trading_path, search4, replace4)

print("Patching complete.")
