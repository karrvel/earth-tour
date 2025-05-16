// Top-level build file where you can add configuration options common to all sub-projects/modules.
buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath("com.android.tools.build:gradle:8.10.0") // Updated to be compatible with Gradle 8.6
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.10") // Updated to 1.9.10 to match Compose Compiler 1.5.3
    }
}

// Remove the allprojects block since repositories are defined in settings.gradle.kts
// This avoids the conflict with repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)

tasks.register("clean", Delete::class) {
    delete(rootProject.layout.buildDirectory)
}
