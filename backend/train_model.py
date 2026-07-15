"""
Plant Disease Detection Model Training Script
==============================================

This script demonstrates the training process for the MobileNetV2 model
used in FarmLens for plant disease detection.

Dataset: PlantVillage (38 classes)
Architecture: MobileNetV2 (Transfer Learning)
Framework: PyTorch

Author: FarmLens Team
Date: 2026
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
import json
import time
import copy
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Configuration
CONFIG = {
    'data_dir': './dataset',  # Path to PlantVillage dataset
    'model_save_path': 'mobilenetv2_plant.pth',
    'class_names_path': 'class_names.json',
    'num_epochs': 25,
    'batch_size': 32,
    'learning_rate': 0.001,
    'num_workers': 4,
    'device': 'cuda' if torch.cuda.is_available() else 'cpu',
    'image_size': 224,
}

print("=" * 70)
print("FARMLENS - PLANT DISEASE DETECTION MODEL TRAINING")
print("=" * 70)
print(f"\nConfiguration:")
print(f"  Device: {CONFIG['device']}")
print(f"  Epochs: {CONFIG['num_epochs']}")
print(f"  Batch Size: {CONFIG['batch_size']}")
print(f"  Learning Rate: {CONFIG['learning_rate']}")
print(f"  Image Size: {CONFIG['image_size']}x{CONFIG['image_size']}")
print("=" * 70)


def prepare_data():
    """
    Prepare data loaders with augmentation for training and validation
    """
    print("\n[1/6] Preparing Data Loaders...")
    
    # Data augmentation for training
    train_transforms = transforms.Compose([
        transforms.Resize((CONFIG['image_size'], CONFIG['image_size'])),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    # No augmentation for validation
    val_transforms = transforms.Compose([
        transforms.Resize((CONFIG['image_size'], CONFIG['image_size'])),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    # Load datasets
    train_dataset = datasets.ImageFolder(
        root=f"{CONFIG['data_dir']}/train",
        transform=train_transforms
    )
    
    val_dataset = datasets.ImageFolder(
        root=f"{CONFIG['data_dir']}/valid",
        transform=val_transforms
    )
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=CONFIG['batch_size'],
        shuffle=True,
        num_workers=CONFIG['num_workers'],
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=CONFIG['batch_size'],
        shuffle=False,
        num_workers=CONFIG['num_workers'],
        pin_memory=True
    )
    
    # Save class names
    class_names = train_dataset.classes
    with open(CONFIG['class_names_path'], 'w') as f:
        json.dump(class_names, f, indent=2)
    
    print(f"  ✓ Training samples: {len(train_dataset)}")
    print(f"  ✓ Validation samples: {len(val_dataset)}")
    print(f"  ✓ Number of classes: {len(class_names)}")
    print(f"  ✓ Class names saved to: {CONFIG['class_names_path']}")
    
    return train_loader, val_loader, class_names


def build_model(num_classes):
    """
    Build MobileNetV2 model with transfer learning
    """
    print("\n[2/6] Building Model...")
    
    # Load pre-trained MobileNetV2
    model = models.mobilenet_v2(pretrained=True)
    
    # Freeze early layers (transfer learning)
    for param in model.features.parameters():
        param.requires_grad = False
    
    # Replace classifier for our number of classes
    model.classifier[1] = nn.Sequential(
        nn.Dropout(0.2),
        nn.Linear(model.classifier[1].in_features, num_classes)
    )
    
    model = model.to(CONFIG['device'])
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"  ✓ Model: MobileNetV2")
    print(f"  ✓ Total parameters: {total_params:,}")
    print(f"  ✓ Trainable parameters: {trainable_params:,}")
    print(f"  ✓ Frozen parameters: {total_params - trainable_params:,}")
    
    return model


def train_model(model, train_loader, val_loader, num_epochs):
    """
    Train the model and track metrics
    """
    print("\n[3/6] Training Model...")
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=CONFIG['learning_rate'])
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.1)
    
    # Tracking metrics
    history = {
        'train_loss': [],
        'train_acc': [],
        'val_loss': [],
        'val_acc': []
    }
    
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0
    
    start_time = time.time()
    
    for epoch in range(num_epochs):
        print(f"\n  Epoch {epoch + 1}/{num_epochs}")
        print("  " + "-" * 50)
        
        # Training phase
        model.train()
        running_loss = 0.0
        running_corrects = 0
        
        for inputs, labels in train_loader:
            inputs = inputs.to(CONFIG['device'])
            labels = labels.to(CONFIG['device'])
            
            optimizer.zero_grad()
            
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            _, preds = torch.max(outputs, 1)
            
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)
        
        epoch_loss = running_loss / len(train_loader.dataset)
        epoch_acc = running_corrects.double() / len(train_loader.dataset)
        
        history['train_loss'].append(epoch_loss)
        history['train_acc'].append(epoch_acc.item())
        
        print(f"  Train Loss: {epoch_loss:.4f} | Train Acc: {epoch_acc:.4f}")
        
        # Validation phase
        model.eval()
        running_loss = 0.0
        running_corrects = 0
        
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs = inputs.to(CONFIG['device'])
                labels = labels.to(CONFIG['device'])
                
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                _, preds = torch.max(outputs, 1)
                
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
        
        epoch_loss = running_loss / len(val_loader.dataset)
        epoch_acc = running_corrects.double() / len(val_loader.dataset)
        
        history['val_loss'].append(epoch_loss)
        history['val_acc'].append(epoch_acc.item())
        
        print(f"  Val Loss:   {epoch_loss:.4f} | Val Acc:   {epoch_acc:.4f}")
        
        # Save best model
        if epoch_acc > best_acc:
            best_acc = epoch_acc
            best_model_wts = copy.deepcopy(model.state_dict())
            print(f"  ✓ New best model! Accuracy: {best_acc:.4f}")
        
        scheduler.step()
    
    time_elapsed = time.time() - start_time
    print(f"\n  Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s")
    print(f"  Best validation accuracy: {best_acc:.4f}")
    
    # Load best model weights
    model.load_state_dict(best_model_wts)
    
    return model, history


def evaluate_model(model, val_loader, class_names):
    """
    Evaluate model and generate detailed metrics
    """
    print("\n[4/6] Evaluating Model...")
    
    model.eval()
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs = inputs.to(CONFIG['device'])
            labels = labels.to(CONFIG['device'])
            
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    # Calculate per-class accuracy
    from sklearn.metrics import classification_report, confusion_matrix
    
    print("\n  Classification Report:")
    print(classification_report(all_labels, all_preds, target_names=class_names, zero_division=0))
    
    # Overall accuracy
    accuracy = np.mean(np.array(all_preds) == np.array(all_labels))
    print(f"\n  ✓ Overall Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    return all_preds, all_labels


def save_model(model):
    """
    Save the trained model
    """
    print(f"\n[5/6] Saving Model...")
    
    torch.save(model.state_dict(), CONFIG['model_save_path'])
    
    print(f"  ✓ Model saved to: {CONFIG['model_save_path']}")
    print(f"  ✓ Model size: {Path(CONFIG['model_save_path']).stat().st_size / (1024*1024):.2f} MB")


def plot_training_history(history):
    """
    Plot training and validation metrics
    """
    print("\n[6/6] Generating Training Plots...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    # Plot loss
    ax1.plot(history['train_loss'], label='Train Loss', marker='o')
    ax1.plot(history['val_loss'], label='Val Loss', marker='s')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title('Training and Validation Loss')
    ax1.legend()
    ax1.grid(True)
    
    # Plot accuracy
    ax2.plot(history['train_acc'], label='Train Accuracy', marker='o')
    ax2.plot(history['val_acc'], label='Val Accuracy', marker='s')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy')
    ax2.set_title('Training and Validation Accuracy')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('training_history.png', dpi=300, bbox_inches='tight')
    
    print(f"  ✓ Training plots saved to: training_history.png")


def main():
    """
    Main training pipeline
    """
    try:
        # Step 1: Prepare data
        train_loader, val_loader, class_names = prepare_data()
        
        # Step 2: Build model
        model = build_model(len(class_names))
        
        # Step 3: Train model
        model, history = train_model(model, train_loader, val_loader, CONFIG['num_epochs'])
        
        # Step 4: Evaluate model
        evaluate_model(model, val_loader, class_names)
        
        # Step 5: Save model
        save_model(model)
        
        # Step 6: Plot results
        plot_training_history(history)
        
        print("\n" + "=" * 70)
        print("TRAINING COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\nModel saved to: {CONFIG['model_save_path']}")
        print(f"Class names saved to: {CONFIG['class_names_path']}")
        print(f"Training plots saved to: training_history.png")
        print("\nYou can now use this model in your FarmLens application!")
        
    except Exception as e:
        print(f"\n❌ Error during training: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
