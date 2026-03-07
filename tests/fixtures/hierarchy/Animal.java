package com.example.animals;

public class Animal {
    private String name;

    public void process(String input) {
        System.out.println("Animal processing: " + input);
    }

    public String getName() {
        return name;
    }

    public void uniqueMethod() {
        // Only in Animal, no overrides
    }
}
