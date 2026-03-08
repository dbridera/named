package com.example.animals;

public class Dog extends Animal {
    @Override
    public void process(String input) {
        System.out.println("Dog processing: " + input);
    }

    public void fetch() {
        // Dog-specific method
    }
}
