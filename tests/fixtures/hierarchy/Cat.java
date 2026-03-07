package com.example.animals;

public class Cat extends Animal {
    @Override
    public void process(String input) {
        System.out.println("Cat processing: " + input);
    }
}
