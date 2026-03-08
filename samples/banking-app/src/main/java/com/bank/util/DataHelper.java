package com.bank.util;

import java.util.Date;
import java.util.List;

/**
 * Utility class with naming anti-patterns.
 * Note: Even the class name "DataHelper" violates R1 (generic) and R3 (noise words).
 */
public class DataHelper {  // R1, R3: Generic class name

    // R1: Constants with vague names
    public static final int MAX = 100;        // Max what?
    public static final String DEFAULT = "";  // Default for what?
    public static final double RATE = 0.05;   // What rate?

    // R4: Unpronounceable timestamp format
    private Date genymdhms;  // generationYearMonthDayHourMinuteSecond
    private Date modymdhms;  // modificationYearMonthDayHourMinuteSecond

    // R6: Single letter class-level variables (very bad)
    private int n;
    private String s;
    private Object o;
    private List<?> l;

    // R1: What do these methods do?
    public static void init() {
        // Initialize what?
    }

    public static Object convert(Object input) {
        // Convert to what?
        return input;
    }

    public static boolean check(String value) {
        // Check what condition?
        return value != null;
    }

    public static String format(Object data) {
        // Format how?
        return data.toString();
    }

    // R3: Methods with noise words
    public static String processTheData(String theData) {
        return theData;
    }

    public static void handleTheRequest(Object theRequest) {
        // noise words everywhere
    }

    // R5: Hungarian notation in methods
    public static String strFormat(String input) {
        return input;
    }

    public static int intParse(String input) {
        return Integer.parseInt(input);
    }

    public static boolean boolCheck(Object obj) {
        return obj != null;
    }

    public static String formatCurrency(double amount) {
        return String.format("$%.2f", amount);
    }

    public static boolean isValidAccountNumber(String accountNumber) {
        return accountNumber != null && accountNumber.length() == 10;
    }

    public static Date parseTransactionDate(String dateString) {
        return new Date();
    }

    // R7: Inconsistent verb usage
    public static void makeActive(Object obj) {}
    public static void setInactive(Object obj) {}
    public static void doEnable(Object obj) {}
    public static void performDisable(Object obj) {}
    // Should all use consistent pattern: activate/deactivate or enable/disable
}
